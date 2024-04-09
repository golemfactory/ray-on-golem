import asyncio
import logging
from datetime import timedelta
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from golem.exceptions import GolemException
from golem.managers.base import ManagerException, WorkContext
from golem.resources import Activity
from golem.utils.asyncio import create_task_with_logging, ensure_cancelled
from golem.utils.logging import get_trace_id_name

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.cluster.sidecars import (
    ActivityStateMonitorClusterNodeSidecar,
    ClusterNodeSidecar,
    HeadNodeToWebserverTunnelClusterNodeSidecar,
    SshStateMonitorClusterNodeSidecar,
)
from ray_on_golem.server.models import NodeConfigData, NodeData, NodeState
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.services.new_golem import GolemService
from ray_on_golem.utils import get_ssh_command, get_ssh_command_args, run_subprocess_output

if TYPE_CHECKING:
    from ray_on_golem.server.cluster import Cluster

logger = logging.getLogger(__name__)


class ClusterNode(NodeData):
    node_config: NodeConfigData
    ssh_private_key_path: Path
    ssh_public_key_path: Path
    ssh_user: str

    _cluster: "Cluster"
    _golem_service: GolemService
    _manager_stack: ManagerStack
    _sidecars: Iterable[ClusterNodeSidecar]
    _ssh_public_key_data: str

    _activity: Optional[Activity] = None
    _start_task: Optional[asyncio.Task] = None

    class Config:
        underscore_attrs_are_private = True

    def __init__(
        self, cluster: "Cluster", golem_service: GolemService, manager_stack: ManagerStack, **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self._cluster = cluster
        self._golem_service = golem_service
        self._manager_stack = manager_stack

        self._sidecars = self._prepare_sidecars()

        with self.ssh_public_key_path.open() as f:
            self._ssh_public_key_data = f.readline().strip()

    def __str__(self) -> str:
        return self.node_id

    def get_data(self) -> NodeData:
        return NodeData.parse_obj(self)

    @property
    def activity(self) -> Optional[Activity]:
        return self._activity

    def start(self) -> None:
        if self.state in (NodeState.running, NodeState.terminating):
            logger.info(f"Not starting `%s` node, as it's already running or stopping", self)
            return

        self._start_task = create_task_with_logging(
            self._start(),
            trace_id=get_trace_id_name(self, "request-node"),
        )

    async def _start(self) -> None:
        logger.info("Starting `%s` node...", self)

        self.state = NodeState.pending

        try:
            while True:
                try:
                    activity, ip, ssh_proxy_command = await self._create_activity()
                except ManagerException:
                    # ManagerException have non-recoverable severity
                    raise
                except (GolemException, RayOnGolemError) as e:
                    msg = "Failed to create activity, retrying."
                    error = f"{type(e).__module__}.{type(e).__name__}: {e}"
                    self._add_state_log(f"{msg} {error=}")
                    logger.warning(msg)
                    logger.debug(msg, exc_info=True)
                else:
                    break
        except Exception as e:
            self.state = NodeState.terminated
            self._add_state_log(
                f"Failed to create activity: {type(e).__module__}.{type(e).__name__}: {e}"
            )

            logger.info("Starting `%s` node failed!", self)

            return

        self._print_ssh_command(ip, ssh_proxy_command)

        self.state = NodeState.running
        self.internal_ip = ip
        self.ssh_proxy_command = ssh_proxy_command

        self._activity = activity

        await self._start_sidecars()

        logger.info("Starting `%s` done", self)

    async def stop(self) -> None:
        if self.state in (NodeState.terminating, NodeState.terminated):
            logger.info(f"Not stopping `%s` node, as it's already stopped", self)
            return

        logger.info("Stopping `%s` node...", self)

        self.state = NodeState.terminating

        if self._start_task:
            await ensure_cancelled(self._start_task)
            self._start_task = None

        await self._stop_sidecars()

        if self._activity:
            await self._stop_activity(self._activity)
            self._activity = None

        self.state = NodeState.terminated
        self.internal_ip = None
        self.ssh_proxy_command = None

        logger.info("Stopping `%s` node done", self)

    def _add_state_log(self, log_entry: str) -> None:
        self.state_log.append(log_entry)

    @staticmethod
    async def _get_provider_desc(activity: Activity) -> str:
        proposal = activity.agreement.proposal
        return f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"

    async def _create_activity(self) -> Tuple[Activity, str, str]:
        logger.info("Creating new activity...")

        self._add_state_log("[1/9] Getting agreement...")

        agreement = await self._manager_stack.get_agreement()

        proposal = agreement.proposal
        provider_desc = f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"
        self._add_state_log(f"[2/9] Creating activity on provider: {provider_desc}...")
        activity: Activity = await agreement.create_activity()
        try:
            self._add_state_log("[3/9] Adding activity to internal VPN...")
            ip = await self._golem_service.add_provider_to_network(
                activity.parent.parent.data.issuer_id
            )
            connection_uri = self._golem_service.get_connection_uri(ip)
            ssh_proxy_command = self._golem_service.get_ssh_proxy_command(connection_uri)

            work_context = WorkContext(activity)

            self._add_state_log("[4/9] Deploying image...")
            await self._deploy_activity(work_context, ip, provider_desc)

            self._add_state_log("[5/9] Starting VM container...")
            await self._start_activity(work_context, ip, provider_desc)

            self._add_state_log("[6/9] Running bootstrap commands...")
            await self._upload_node_configuration(
                work_context, ip, self._ssh_public_key_data, provider_desc
            )

            self._add_state_log("[7/9] Starting ssh service...")
            await self._start_ssh_server(work_context, ip, provider_desc)

            self._add_state_log("[8/9] Checking SSH connection...")
            await self.verify_ssh_connection(activity, ip, ssh_proxy_command)

            await self._golem_service.refresh_network_nodes()
        except Exception as e:
            logger.exception(f"Creating new activity failed with `%s`", f"{type(e).__name__}: {e}")
            await self._stop_activity(activity)
            raise

        self._add_state_log(f"[9/9] Activity ready on provider: {provider_desc}")

        logger.info(f"Creating new activity done on {provider_desc}, {ip=}, {activity=}")

        return activity, ip, ssh_proxy_command

    async def _deploy_activity(self, context: WorkContext, ip: str, provider_desc: str) -> None:
        activity = context.activity
        logger.info(f"Deploying image on {provider_desc}, {ip=}, {activity=}")

        deploy_args = {"net": [self._golem_service.get_deploy_args(ip)]}
        await context.deploy(deploy_args, timeout=timedelta(minutes=5))

    async def _start_activity(self, context: WorkContext, ip: str, provider_desc: str) -> None:
        activity = context.activity
        logger.info(f"Starting VM container on {provider_desc}, {ip=}, {activity=}")

        await context.start()

    async def _upload_node_configuration(
        self,
        context: WorkContext,
        ip: str,
        ssh_public_key_data: str,
        provider_desc: str,
    ) -> None:
        logger.info(f"Running initial commands on {provider_desc}, {ip=}, {context.activity=}")

        hostname = ip.replace(".", "-")

        await context.run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        await context.run(f"echo 'NODE_IP={ip}' >> /etc/environment")
        await context.run(f"hostname '{hostname}'")
        await context.run(f"echo '{hostname}' > /etc/hostname")
        await context.run(f"echo '{ip} {hostname}' >> /etc/hosts")
        await context.run("mkdir -p /root/.ssh")
        await context.run(f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys')

    async def _start_ssh_server(self, context: WorkContext, ip: str, provider_desc: str):
        logger.info(f"Starting ssh service on {provider_desc}, {ip=}, {context.activity=}")

        await context.run("service ssh start")

    async def restart_ssh_server(
        self, context: Optional[WorkContext] = None, ip: Optional[str] = None
    ):
        context = WorkContext(self._activity) if context is None else context
        ip = self.internal_ip if ip is None else ip

        provider_desc = await self._get_provider_desc(context.activity)
        logger.debug(f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=}")
        try:
            await context.run("service ssh restart", timeout=120)
        except Exception:
            msg = f"Failed to restart SSH server {provider_desc}, {ip=}, {context.activity=}"
            logger.warning(msg)
            logger.debug(msg, exc_info=True)
        else:
            logger.debug(
                f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=} done"
            )

    async def verify_ssh_connection(
        self,
        activity: Optional[Activity] = None,
        ip: Optional[str] = None,
        ssh_proxy_command: Optional[str] = None,
        num_retries=3,
        retry_interval=1,
    ) -> None:
        activity = self._activity if activity is None else activity
        ip = self.internal_ip if ip is None else ip
        ssh_proxy_command = (
            self.ssh_proxy_command if ssh_proxy_command is None else ssh_proxy_command
        )

        provider_desc = await self._get_provider_desc(activity)

        logger.info(f"SSH connection check on {provider_desc}, {ip=}, {activity=}...")

        ssh_command_parts = [
            *get_ssh_command_args(ip, ssh_proxy_command, self.ssh_user, self.ssh_private_key_path),
            "uptime",
        ]

        retry = num_retries
        while True:
            try:
                await run_subprocess_output(*ssh_command_parts)
            except RayOnGolemError as e:
                retry -= 1
                if 0 < retry:
                    logger.info(
                        f"SSH connection check on {provider_desc}, {ip=}, {activity=} failed, retrying {retry}..."
                    )
                    await asyncio.sleep(retry_interval)
                else:
                    logger.info(
                        f"SSH connection check on {provider_desc}, {ip=}, {activity=} failed after {num_retries} tries!"
                    )
                    raise RayOnGolemError(
                        f"SSH connection check failed after {num_retries} tries!"
                    ) from e
            else:
                break

        logger.info(f"SSH connection check on {provider_desc}, {ip=}, {activity=} done")

    async def _stop_activity(self, activity: Activity) -> None:
        provider_desc = await self._get_provider_desc(activity)
        try:
            await activity.destroy()
        except Exception:
            logger.debug(f"Cannot destroy activity {provider_desc}", exc_info=True)

    def _print_ssh_command(self, ip: str, ssh_proxy_command: str) -> None:
        ssh_command = get_ssh_command(
            ip, ssh_proxy_command, self.ssh_user, self.ssh_private_key_path
        )

        logger.debug("Connect to `%s` with:\n%s", ip, ssh_command)

    def _prepare_sidecars(self) -> Iterable[ClusterNodeSidecar]:
        return []

    async def _start_sidecars(self) -> None:
        logger.info("Starting `%s` node sidecars...", self)

        await asyncio.gather(*[sidecar.start() for sidecar in self._sidecars])

        logger.info("Starting `%s` node sidecars done", self)

    async def _stop_sidecars(self) -> None:
        logger.info("Stopping `%s` node sidecars...", self)

        await asyncio.gather(*[sidecar.stop() for sidecar in self._sidecars])

        logger.info("Stopping `%s` node sidecars done", self)


class WorkerClusterNode(ClusterNode):
    def _prepare_sidecars(self) -> Iterable[ClusterNodeSidecar]:
        return (
            ActivityStateMonitorClusterNodeSidecar(
                self,
                cluster=self._cluster,
                check_interval=timedelta(minutes=1, seconds=30),
            ),
            SshStateMonitorClusterNodeSidecar(
                self,
                check_interval=timedelta(minutes=2),
                max_fail_count=3,
            ),
        )


class HeadClusterNode(ClusterNode):
    webserver_port: int

    def _prepare_sidecars(self) -> Iterable[ClusterNodeSidecar]:
        return chain(
            super()._prepare_sidecars(), (HeadNodeToWebserverTunnelClusterNodeSidecar(self),)
        )
