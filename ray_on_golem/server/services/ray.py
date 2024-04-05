import asyncio
import logging
from asyncio.subprocess import Process
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from golem.resources import Activity
from golem.utils.asyncio import create_task_with_logging, ensure_cancelled, ensure_cancelled_many
from golem.utils.logging import get_trace_id_name
from ray.autoscaler.tags import NODE_KIND_HEAD, TAG_RAY_NODE_KIND, TAG_RAY_USER_NODE_TYPE

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.exceptions import NodeNotFound
from ray_on_golem.server.models import (
    Node,
    NodeConfigData,
    NodeData,
    NodeId,
    NodeState,
    ProviderConfigData,
    Tags,
)
from ray_on_golem.server.services.golem import GolemService
from ray_on_golem.server.services.utils import get_ssh_command
from ray_on_golem.server.services.yagna import YagnaService
from ray_on_golem.utils import (
    are_dicts_equal,
    get_default_ssh_key_name,
    run_subprocess,
    run_subprocess_output,
)

logger = logging.getLogger(__name__)


DEFAULT_NODE_MONITORING_TIMEOUT = timedelta(minutes=1, seconds=30)


class RayServiceError(RayOnGolemError):
    pass


class RayService:
    def __init__(
        self,
        ray_on_golem_port: int,
        golem_service: GolemService,
        yagna_service: YagnaService,
        datadir: Path,
        node_monitoring_timeout: timedelta = DEFAULT_NODE_MONITORING_TIMEOUT,
    ):
        self._ray_on_golem_port = ray_on_golem_port
        self._golem_service = golem_service
        self._yagna_service = yagna_service
        self._datadir = datadir

        self._provider_config: Optional[ProviderConfigData] = None
        self._cluster_name: Optional[str] = None
        self._wallet_address: Optional[str] = None
        self._cluster_running: bool = True

        self._nodes: Dict[NodeId, Node] = {}
        self._nodes_lock = asyncio.Lock()
        self._nodes_id_counter = 0

        self._create_node_tasks: Dict[NodeId, asyncio.Task] = {}
        self._node_monitoring_tasks: Dict[NodeId, asyncio.Task] = {}
        self._node_monitoring_timeout: timedelta = node_monitoring_timeout

        self._head_node_to_webserver_tunnel_process: Optional[Process] = None
        self._head_node_to_webserver_tunnel_early_exit_task: Optional[asyncio.Task] = None

        self._ssh_private_key_path: Optional[Path] = None
        self._ssh_public_key_path: Optional[Path] = None
        self._ssh_public_key: Optional[str] = None
        self._ssh_user: Optional[str] = None

    async def shutdown(self) -> None:
        logger.info("Stopping RayService...")
        await self._stop_node_monitoring_tasks()
        await self._stop_head_node_to_webserver_tunnel()
        await self._stop_create_node_tasks()
        await self._destroy_nodes()

        logger.info("Stopping RayService done")

    async def create_cluster(
        self, provider_config: ProviderConfigData, cluster_name: str
    ) -> Tuple[bool, str, str, Dict]:
        is_cluster_just_created = self._provider_config is None

        if not is_cluster_just_created and self._cluster_name != cluster_name:
            raise RayServiceError(
                f"Webserver is running only for `{self._cluster_name}` cluster, not for `{cluster_name}`!"
            )

        self._provider_config = provider_config
        self._cluster_name = cluster_name

        self._ssh_private_key_path = Path(provider_config.ssh_private_key)
        self._ssh_public_key_path = self._ssh_private_key_path.with_suffix(".pub")
        self._ssh_user = provider_config.ssh_user

        with self._ssh_public_key_path.open() as f:
            self._ssh_public_key = f.readline().strip()

        payment_status = await self._yagna_service.prepare_funds(
            self._provider_config.payment_network,
            self._provider_config.payment_driver,
        )
        yagna_output = await self._yagna_service.fetch_payment_status(
            self._provider_config.payment_network,
            self._provider_config.payment_driver,
        )
        self._wallet_address = await self._yagna_service.fetch_wallet_address()

        return is_cluster_just_created, self._wallet_address, yagna_output, payment_status

    async def _destroy_nodes(self) -> None:
        async with self._nodes_lock:
            if not self._nodes:
                logger.info("Not destroying nodes, as no nodes are running")
                return

            logger.info(f"Destroying {len(self._nodes)} nodes...")

            await asyncio.gather(
                *[
                    self._golem_service.stop_activity(node.activity)
                    for node in self._nodes.values()
                    if node.activity is not None
                ]
            )

            logger.info(f"Destroying {len(self._nodes)} nodes done")

            self._nodes.clear()

    async def request_nodes(
        self, node_config: Dict[str, Any], count: int, tags: Tags
    ) -> List[NodeId]:
        # TODO: Use node_config from yaml.available_node_types not, from yaml.provider

        if not self._provider_config:
            raise RayServiceError("Node requesting is available only after cluster bootstrap!")

        if not self._cluster_running:
            raise RayServiceError("Node requesting is not available after downing cluster!")

        created_node_ids = []
        async with self._nodes_lock:
            for _ in range(count):
                node_id = self._get_new_node_id()
                created_node_ids.append(node_id)

                self._nodes[node_id] = Node(
                    node_id=node_id,
                    tags=tags,
                )

                self._create_node_tasks[node_id] = create_task_with_logging(
                    self._create_node(
                        node_id,
                        NodeConfigData(**node_config),
                        node_type=self._get_node_type(tags),
                        is_head_node=self._is_head_node(tags),
                    ),
                    trace_id=get_trace_id_name(self, f"create-node-{node_id}"),
                )

        logger.info(f"Requested {count} nodes")
        logger.debug(f"{self._provider_config=}")

        return created_node_ids

    async def _create_node(
        self, node_id: NodeId, node_config: NodeConfigData, node_type: str, is_head_node: bool
    ) -> None:
        logger.info("Creating node `%s`...", node_id)

        try:
            activity, ip, ssh_proxy_command = await self._golem_service.create_activity(
                node_config=node_config,
                public_ssh_key=self._ssh_public_key,
                ssh_user=self._ssh_user,
                ssh_private_key_path=self._ssh_private_key_path,
                total_budget=self._provider_config.total_budget,
                payment_network=self._provider_config.payment_network,
                payment_driver=self._provider_config.payment_driver,
                add_state_log=partial(self._add_node_state_log, node_id),
                node_type=node_type,
                is_head_node=is_head_node,
            )

            self._print_ssh_command(
                ip, ssh_proxy_command, self._ssh_user, self._ssh_private_key_path
            )

            async with self._get_node_context(node_id) as node:  # type: Node
                node.state = NodeState.running
                node.internal_ip = ip
                node.ssh_proxy_command = ssh_proxy_command
                node.activity = activity

            # TODO: check if node is a head node
            if not self._is_head_node_to_webserver_tunnel_running():
                await self._start_head_node_to_webserver_tunnel()

            # monitor activity state
            self._node_monitoring_tasks[node_id] = create_task_with_logging(
                self._monitor_node(node_id, activity)
            )
        except Exception as e:
            async with self._get_node_context(node_id) as node:  # type: Node
                node.state = NodeState.terminated
                node.state_log.append(
                    f"Failed to create activity: {type(e).__module__}.{type(e).__name__}: {e}"
                )
        finally:
            del self._create_node_tasks[node_id]

        logger.info("Creating node `%s` done", node_id)

    async def _add_node_state_log(self, node_id: NodeId, log_entry: str) -> None:
        async with self._get_node_context(node_id) as node:  # type: Node
            node.state_log.append(log_entry)

    def _get_new_node_id(self) -> NodeId:
        node_id = f"node{self._nodes_id_counter}"
        self._nodes_id_counter += 1
        return node_id

    async def _monitor_node(self, node_id: NodeId, activity: Activity) -> None:
        async with self._get_node_context(node_id) as node:  # type: Node
            is_head_node = self._is_head_node(node.tags)
        while self._cluster_running:
            try:
                activity_state = await activity.get_state()
                if (
                    "Terminated" in activity_state.state
                    or "Unresponsive" in activity_state.state
                    or activity_state.error_message is not None
                ):
                    raise RayServiceError(
                        f"Something is wrong with node {node_id} activity. {activity_state=}"
                    )
            except Exception:
                msg = (
                    f"Activity on {await self._golem_service.get_provider_desc(activity)} "
                    f"is no longer accessible. Terminating {node_id} {is_head_node=}"
                )
                logger.warning(msg)
                logger.debug(msg, exc_info=True)
                if is_head_node:
                    self._cluster_running = False
                    create_task_with_logging(self.shutdown())
                else:
                    create_task_with_logging(self.terminate_node(node_id))
                break
            await asyncio.sleep(self._node_monitoring_timeout.total_seconds())

    async def terminate_node(self, node_id: NodeId) -> Dict[NodeId, Dict]:
        logger.info("Terminating node `%s`...", node_id)

        if node_id in self._node_monitoring_tasks:
            logger.debug("Cancelling node `%s` monitoring task...")
            await ensure_cancelled(self._node_monitoring_tasks[node_id])
            logger.debug("Cancelling node `%s` monitoring task done")

        if node_id in self._create_node_tasks:
            logger.debug("Cancelling node `%s` creation request...")
            await ensure_cancelled(self._create_node_tasks[node_id])
            logger.debug("Cancelling node `%s` creation request done")

        async with self._get_node_context(node_id) as node:  # type: Node
            node.state = NodeState.terminating

        if node.activity:
            await self._golem_service.stop_activity(node.activity)

        async with self._get_node_context(node_id) as node:  # type: Node
            node.state = NodeState.terminated
            node.activity = None

            logger.info(f"Terminating node `%s` done", node_id)

            results = {node.node_id: node.dict(exclude={"activity"})}

        async with self._nodes_lock:
            if all(node.state == NodeState.terminated for node in self._nodes.values()):
                logger.info("All nodes are terminated, terminating whole cluster.")
                self._cluster_running = False
                await self._stop_head_node_to_webserver_tunnel()
                await self._golem_service.clear()

        return results

    async def get_cluster_data(self) -> Dict[NodeId, NodeData]:
        async with self._nodes_lock:
            return {node.node_id: NodeData.parse_obj(node) for node in self._nodes.values()}

    async def get_non_terminated_nodes_ids(
        self, tags_to_match: Optional[Dict[str, str]] = None
    ) -> List[NodeId]:
        async with self._nodes_lock:
            nodes = [
                node
                for node in self._nodes.values()
                if node.state not in [NodeState.terminating, NodeState.terminated]
            ]

        if tags_to_match is None:
            return [node.node_id for node in nodes]

        return [node.node_id for node in nodes if are_dicts_equal(node.tags, tags_to_match)]

    async def is_node_running(self, node_id: NodeId) -> bool:
        async with self._get_node_context(node_id) as node:  # type: Node
            return node.state == NodeState.running

    async def is_node_terminated(self, node_id: NodeId) -> bool:
        async with self._get_node_context(node_id) as node:  # type: Node
            return node.state in [NodeState.terminating, NodeState.terminated]

    async def get_node_tags(self, node_id: NodeId) -> Dict:
        async with self._get_node_context(node_id) as node:  # type: Node
            return node.tags

    async def get_node_internal_ip(self, node_id: NodeId) -> Optional[str]:
        async with self._get_node_context(node_id) as node:  # type: Node
            return node.internal_ip

    async def get_ssh_proxy_command(self, node_id: NodeId) -> Optional[str]:
        async with self._get_node_context(node_id) as node:  # type: Node
            return node.ssh_proxy_command

    async def set_node_tags(self, node_id: NodeId, tags: Tags) -> None:
        async with self._get_node_context(node_id) as node:  # type: Node
            node.tags.update(tags)

    async def get_or_create_default_ssh_key(self, cluster_name: str) -> Tuple[str, str]:
        ssh_key_path = self._datadir / get_default_ssh_key_name(cluster_name)
        ssk_public_key_path = ssh_key_path.with_suffix(".pub")

        if not ssh_key_path.exists():
            logger.info(f"Creating default ssh key for `{cluster_name}`...")

            ssh_key_path.parent.mkdir(parents=True, exist_ok=True)

            # FIXME: Use cryptography module instead of subprocess
            await run_subprocess_output(
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(ssh_key_path)
            )

            logger.info(
                f"Creating default ssh key for `{cluster_name}` done with path `{ssh_key_path}`"
            )

        # TODO: async file handling
        with ssh_key_path.open("r") as priv_f, ssk_public_key_path.open("r") as pub_f:
            return str(priv_f.read()), str(pub_f.read())

    def get_datadir(self) -> Path:
        return self._datadir

    @asynccontextmanager
    async def _get_node_context(self, node_id: NodeId) -> Iterator[Node]:
        async with self._nodes_lock:
            node = self._nodes.get(node_id)

            if node is None:
                raise NodeNotFound

            yield node

    async def _get_head_node(self) -> Node:
        async with self._nodes_lock:
            for node in self._nodes.values():
                if self._is_head_node(node.tags):
                    return node

            raise NodeNotFound

    @staticmethod
    def _is_head_node(tags: Tags) -> bool:
        return tags.get(TAG_RAY_NODE_KIND) == NODE_KIND_HEAD

    @staticmethod
    def _get_node_type(tags: Tags) -> str:
        return tags.get(TAG_RAY_USER_NODE_TYPE)

    def _print_ssh_command(
        self, ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
    ) -> None:
        logger.debug(
            f"Connect to `{ip}` with:\n"
            f"{get_ssh_command(ip, ssh_proxy_command, ssh_user, ssh_private_key_path)}"
        )

    def _is_head_node_to_webserver_tunnel_running(self) -> bool:
        return self._head_node_to_webserver_tunnel_process is not None

    async def _start_head_node_to_webserver_tunnel(self) -> None:
        logger.info("Starting head node to webserver tunnel...")

        head_node = await self._get_head_node()
        port = self._ray_on_golem_port

        self._head_node_to_webserver_tunnel_process = await run_subprocess(
            "ssh",
            "-N",
            "-R",
            f"*:{port}:127.0.0.1:{port}",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            f"ProxyCommand={head_node.ssh_proxy_command}",
            "-i",
            str(self._ssh_private_key_path),
            f"{self._ssh_user}@{str(head_node.internal_ip)}",
        )
        self._head_node_to_webserver_tunnel_early_exit_task = create_task_with_logging(
            self._on_head_node_to_webserver_tunnel_early_exit()
        )

        logger.info("Starting head node to webserver tunnel done")

    async def _on_head_node_to_webserver_tunnel_early_exit(self) -> None:
        await self._head_node_to_webserver_tunnel_process.communicate()

        logger.warning(f"Head node to webserver tunnel exited prematurely!")

    async def _stop_head_node_to_webserver_tunnel(self) -> None:
        process = self._head_node_to_webserver_tunnel_process

        if process is None or process.returncode is not None:
            logger.info("Not stopping head node to webserver tunnel, as it's not running")
            return

        logger.info("Stopping head node to webserver tunnel...")

        self._head_node_to_webserver_tunnel_early_exit_task.cancel()
        try:
            await self._head_node_to_webserver_tunnel_early_exit_task
        except asyncio.CancelledError:
            pass

        process.terminate()
        await process.wait()

        self._head_node_to_webserver_tunnel_process = None

        logger.info("Stopping head node to webserver tunnel done")

    async def _stop_create_node_tasks(self) -> None:
        task_count = len(self._create_node_tasks)
        if not task_count:
            logger.info("Not canceling pending node creation tasks, as no tasks are pending")
            return

        logger.info("Canceling %d pending node creation tasks...", task_count)

        await ensure_cancelled_many(self._create_node_tasks.values())
        self._create_node_tasks.clear()

        logger.info("Canceling %d pending node creation tasks done", task_count)

    async def _stop_node_monitoring_tasks(self) -> None:
        task_count = len(self._node_monitoring_tasks)
        if not task_count:
            logger.info("Not canceling pending node monitoring tasks, as there are no tasks")
            return

        logger.info("Canceling %d node monitoring tasks...", task_count)

        await ensure_cancelled_many(self._node_monitoring_tasks.values())
        self._node_monitoring_tasks.clear()

        logger.info("Canceling %d node monitoring tasks done", task_count)
