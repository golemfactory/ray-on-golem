import asyncio
import logging
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Collection, List, Optional, Sequence, Tuple

from golem.exceptions import GolemException
from golem.managers.base import ManagerException, WorkContext
from golem.resources import Activity, Agreement, BatchError
from golem.utils.asyncio import create_task_with_logging, ensure_cancelled
from golem.utils.asyncio.tasks import resolve_maybe_awaitable
from golem.utils.logging import get_trace_id_name
from golem.utils.typing import MaybeAwaitable

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.cluster.sidecars import (
    ActivityStateMonitorClusterNodeSidecar,
    ClusterNodeSidecar,
    MonitorClusterNodeSidecar,
    PortTunnelClusterNodeSidecar,
    SshStateMonitorClusterNodeSidecar,
)
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.server.models import NodeConfigData, NodeData, NodeState
from ray_on_golem.server.services import GolemService, ManagerStack
from ray_on_golem.server.settings import (
    CLUSTER_MONITOR_CHECK_INTERVAL,
    CLUSTER_MONITOR_RETRY_COUNT,
    CLUSTER_MONITOR_RETRY_INTERVAL,
)
from ray_on_golem.server.utils import get_provider_desc
from ray_on_golem.utils import get_ssh_command, get_ssh_command_args, run_subprocess_output

if TYPE_CHECKING:
    from ray_on_golem.server.cluster import Cluster

RAY_GCS_PORT = 6379
RAY_DASHBOARD_PORT = 8265

logger = logging.getLogger(__name__)


class ClusterNode(WarningMessagesMixin, NodeData):
    """Self-contained element that represents Ray node."""

    node_config: NodeConfigData
    ssh_private_key_path: Path
    ssh_public_key_path: Path
    ssh_user: str

    _cluster: "Cluster"
    _golem_service: GolemService
    _manager_stack: ManagerStack

    _sidecars: Collection[ClusterNodeSidecar]
    _ssh_public_key_data: str

    _priority_agreement_timeout: timedelta
    _priority_manager_stack: Optional[ManagerStack] = None
    _activity: Optional[Activity] = None
    _start_task: Optional[asyncio.Task] = None
    _warning_messages: List[str] = None
    _on_stop: Optional[Callable[["ClusterNode"], MaybeAwaitable[None]]] = None

    def __init__(
        self,
        cluster: "Cluster",
        golem_service: GolemService,
        manager_stack: ManagerStack,
        priority_agreement_timeout: timedelta,
        priority_manager_stack: Optional[ManagerStack] = None,
        on_stop: Optional[Callable[["ClusterNode"], MaybeAwaitable[None]]] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._cluster = cluster
        self._golem_service = golem_service
        self._manager_stack = manager_stack
        self._priority_manager_stack = priority_manager_stack
        self._priority_agreement_timeout = priority_agreement_timeout
        self._on_stop = on_stop

        self._sidecars = self._prepare_sidecars()

        with self.ssh_public_key_path.open() as f:
            self._ssh_public_key_data = f.readline().strip()

    def __str__(self) -> str:
        return self.node_id

    def get_data(self) -> NodeData:
        """Return model-related data from the node."""

        return NodeData.parse_obj(self)

    @property
    def activity(self) -> Optional[Activity]:
        """Read-only activity related to the node."""

        return self._activity

    @property
    def manager_stacks(self) -> Sequence[ManagerStack]:
        """Read-only manager stack related to the node."""
        manager_stacks = [self._manager_stack]

        if self._priority_manager_stack:
            manager_stacks.append(self._priority_manager_stack)

        return manager_stacks

    def get_warning_messages(self) -> Sequence[str]:
        """Get read-only collection of warnings both from the node and its sidecars."""

        warnings = list(super().get_warning_messages())

        for sidecar in self._sidecars:
            warnings.extend(sidecar.get_warning_messages())

        return warnings

    def schedule_start(self) -> None:
        """Schedule start of the node in another asyncio task."""

        if (self._start_task and not self._start_task.done()) or (
            self.state in (NodeState.running, NodeState.terminating)
        ):
            logger.info(
                f"Not scheduling start `%s` node, as it's already scheduled, running or stopping",
                self,
            )
            return

        self._start_task = create_task_with_logging(
            self.start(),
            trace_id=get_trace_id_name(self, "scheduled-start"),
        )

    async def start(self) -> None:
        """Start the node, its internal state and try to create its activity."""

        if self.state in (NodeState.running, NodeState.terminating):
            logger.info(f"Not starting `%s` node, as it's already running or stopping", self)
            return

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

        logger.info("Starting `%s` node done", self)

    async def stop(self, call_events: bool = True) -> None:
        """Stop the node and cleanup its internal state."""

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

        if self._on_stop and call_events:
            await resolve_maybe_awaitable(self._on_stop(self))

        logger.info("Stopping `%s` node done", self)

    def _add_state_log(self, log_entry: str) -> None:
        self.state_log.append(log_entry)

    async def _create_activity(self) -> Tuple[Activity, str, str]:
        logger.info("Creating new activity...")

        self._add_state_log("[1/9] Getting an agreement...")
        agreement = await self._get_agreement()

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

    async def _get_agreement(self) -> Agreement:
        if self._priority_manager_stack:
            try:
                return await asyncio.wait_for(
                    self._priority_manager_stack.get_agreement(),
                    timeout=self._priority_agreement_timeout.total_seconds(),
                )
            except asyncio.TimeoutError:
                self._add_state_log(
                    "No recommended providers were found. We are extending the search to all "
                    "public providers, which might be less stable. Restart the cluster to try "
                    "finding recommended providers again. If the problem persists please let us "
                    "know at `#Ray on Golem` discord channel (https://chat.golem.network/)"
                )

        return await self._manager_stack.get_agreement()

    async def _deploy_activity(self, context: WorkContext, ip: str, provider_desc: str) -> None:
        activity = context.activity
        logger.info(f"Deploying image on {provider_desc}, {ip=}, {activity=}")

        deploy_args = {"net": [self._golem_service.get_deploy_args(ip)]}
        await context.deploy(deploy_args, timeout=timedelta(minutes=5))

    async def _start_activity(self, context: WorkContext, ip: str, provider_desc: str) -> None:
        activity = context.activity
        logger.info(f"Starting VM container on {provider_desc}, {ip=}, {activity=}")

        await context.start()

    @staticmethod
    async def _run_command(context: WorkContext, cmd: str, timeout: Optional[float] = None):
        result = await context.run(cmd, timeout=timeout)

        try:
            await result.wait()
        except BatchError as e:
            raise RayOnGolemError(f"Executing command `{cmd}` failed!") from e

        logger.debug("Command executed: %s: %s", cmd, [e.to_dict() for e in result.events])

    async def _upload_node_configuration(
        self,
        context: WorkContext,
        ip: str,
        ssh_public_key_data: str,
        provider_desc: str,
    ) -> None:
        logger.info(f"Running initial commands on {provider_desc}, {ip=}, {context.activity=}")

        hostname = ip.replace(".", "-")

        await self._run_command(context, "echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        await self._run_command(context, f"echo 'NODE_IP={ip}' >> /etc/environment")
        await self._run_command(context, f"echo '{hostname}' > /etc/hostname")
        await self._run_command(context, f"echo '{ip} {hostname}' >> /etc/hosts")
        await self._run_command(
            context,
            "mv "
            "/root_copy/.bashrc "
            "/root_copy/.profile "
            "/root_copy/.config "
            "/root_copy/.local "
            "/root_copy/venv "
            "/root 2> /dev/null",
        )
        await self._run_command(context, f"echo 'export PATH=$PATH:/root/.local/bin' >> /root/.bashrc")
        await self._run_command(context, f"echo 'source /root/venv/bin/activate' >> /root/.bashrc")

        await self._run_command(context, "mkdir -p /root/.ssh")
        await self._run_command(
            context, f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys'
        )

    async def _start_ssh_server(self, context: WorkContext, ip: str, provider_desc: str):
        logger.info(f"Starting ssh service on {provider_desc}, {ip=}, {context.activity=}")

        await self._run_command(context, "service ssh start")

    async def restart_ssh_server(
        self, context: Optional[WorkContext] = None, ip: Optional[str] = None
    ):
        """Restart ssh server running on activity related to the node."""

        context = WorkContext(self._activity) if context is None else context
        ip = self.internal_ip if ip is None else ip

        provider_desc = await get_provider_desc(context.activity)
        logger.debug(f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=}...")
        try:
            await self._run_command(context, "service ssh restart", timeout=120)
        except Exception:
            msg = f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=} failed!"
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
    ) -> None:
        """Verify if ssh connection to activity related to the node is working.

        Multiple attempts will be made. `RayOnGolemError` will be thrown if ssh connection is not
        working.
        """

        activity = self._activity if activity is None else activity
        ip = self.internal_ip if ip is None else ip
        ssh_proxy_command = (
            self.ssh_proxy_command if ssh_proxy_command is None else ssh_proxy_command
        )
        provider_desc = await get_provider_desc(activity)

        logger.info(f"SSH connection check on {provider_desc}, {ip=}, {activity=}...")

        ssh_command_parts = [
            *get_ssh_command_args(ip, ssh_proxy_command, self.ssh_user, self.ssh_private_key_path),
            "uptime",
        ]

        num_retries = CLUSTER_MONITOR_RETRY_COUNT
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
                    await asyncio.sleep(CLUSTER_MONITOR_RETRY_INTERVAL.total_seconds())
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
        provider_desc = await get_provider_desc(activity)
        try:
            await activity.destroy()
        except Exception:
            logger.debug(f"Cannot destroy activity {provider_desc}", exc_info=True)

    def _print_ssh_command(self, ip: str, ssh_proxy_command: str) -> None:
        ssh_command = get_ssh_command(
            ip, ssh_proxy_command, self.ssh_user, self.ssh_private_key_path
        )

        logger.debug("Connect to `%s` with:\n%s", ip, ssh_command)

    def _prepare_sidecars(self) -> Collection[ClusterNodeSidecar]:
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
    """Self-contained element that represents explicitly a Ray worker node."""

    def _prepare_sidecars(self) -> Collection[ClusterNodeSidecar]:
        return (
            ActivityStateMonitorClusterNodeSidecar(
                node=self,
                on_monitor_failed_func=self._on_monitor_check_failed,
                check_interval=CLUSTER_MONITOR_CHECK_INTERVAL,
            ),
            SshStateMonitorClusterNodeSidecar(
                node=self,
                on_monitor_failed_func=self._on_monitor_check_failed,
                check_interval=CLUSTER_MONITOR_CHECK_INTERVAL,
                retry_interval=CLUSTER_MONITOR_RETRY_INTERVAL,
                max_fail_count=CLUSTER_MONITOR_RETRY_COUNT,
            ),
        )

    async def _on_monitor_check_failed(
        self, monitor: MonitorClusterNodeSidecar, node: ClusterNode
    ) -> bool:
        provider_desc = await get_provider_desc(self.activity)

        message = f"Terminating node as worker `%s` %s {monitor.name} is no longer accessible"

        logger.warning(message, self.node_id, provider_desc)
        self.add_warning_message(message, self.node_id, provider_desc)

        create_task_with_logging(self.stop())

        return True


class HeadClusterNode(WorkerClusterNode):
    """Self-contained element that represents explicitly a Ray head node."""

    _webserver_port: int
    _ray_gcs_expose_port: Optional[int]

    def __init__(
        self,
        webserver_port: int,
        ray_gcs_expose_port: Optional[int],
        **kwargs,
    ) -> None:
        self._webserver_port = webserver_port
        self._ray_gcs_expose_port = ray_gcs_expose_port

        # Late init as it will trigger `_prepare_sidecars` that requires fields from above
        super().__init__(**kwargs)

    def _prepare_sidecars(self) -> Collection[ClusterNodeSidecar]:
        sidecars = [
            *super()._prepare_sidecars(),
            PortTunnelClusterNodeSidecar(node=self, local_port=self._webserver_port, reverse=True),
        ]

        if self._ray_gcs_expose_port:
            sidecars.append(
                PortTunnelClusterNodeSidecar(
                    node=self, local_port=self._ray_gcs_expose_port, remote_port=RAY_GCS_PORT
                ),
            )

        return sidecars

    async def _on_monitor_check_failed(
        self, monitor: MonitorClusterNodeSidecar, node: ClusterNode
    ) -> bool:
        provider_desc = await get_provider_desc(self.activity)

        message = f"Terminating cluster as head `%s` %s {monitor.name} is no longer accessible"

        logger.warning(message, self.node_id, provider_desc)
        self.add_warning_message(message, self.node_id, provider_desc)

        create_task_with_logging(self._cluster.stop(clear=False))

        return True
