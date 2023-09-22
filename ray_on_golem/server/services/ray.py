import asyncio
import logging
from asyncio.subprocess import Process
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from ray.autoscaler.tags import NODE_KIND_HEAD, TAG_RAY_NODE_KIND

from ray_on_golem.server.exceptions import NodeNotFound
from ray_on_golem.server.models import CreateClusterRequestData, Node, NodeId, NodeState, Tags
from ray_on_golem.server.services.golem import GolemService
from ray_on_golem.utils import (
    are_dicts_equal,
    get_default_ssh_key_name,
    run_subprocess,
    run_subprocess_output,
)

logger = logging.getLogger(__name__)


class RayService:
    def __init__(self, golem_service: GolemService, tmp_path: Path):
        self._golem_service = golem_service
        self._tmp_path = tmp_path

        self._nodes: Dict[NodeId, Node] = {}
        self._nodes_lock = asyncio.Lock()
        self._nodes_id_counter = 0

        self._head_node_to_webserver_tunnel_process: Optional[Process] = None
        self._head_node_to_webserver_tunnel_early_exit_task: Optional[asyncio.Task] = None

        self._ssh_private_key_path: Optional[Path] = None
        self._ssh_public_key_path: Optional[Path] = None

    async def shutdown(self) -> None:
        logger.info("Stopping RayService...")

        await self._stop_head_node_to_webserver_tunnel()
        await self._destroy_nodes()

        logger.info("Stopping RayService done")

    async def create_cluster_on_golem(self, provider_config: CreateClusterRequestData) -> None:
        self._ssh_private_key_path = Path(provider_config.ssh_private_key)
        self._ssh_public_key_path = self._ssh_private_key_path.with_suffix(".pub")
        self._ssh_user = provider_config.ssh_user

        await self._golem_service.create_cluster(provider_config=provider_config)

    async def _destroy_nodes(self) -> None:
        async with self._nodes_lock:
            if not self._nodes:
                logger.info("No need to destroy nodes, as no nodes are running")
                return

            logger.info(f"Destroying {len(self._nodes)} nodes...")

            for node in self._nodes.values():
                await node.activity.destroy()

            logger.info(f"Destroying {len(self._nodes)} nodes done")

            self._nodes.clear()

    async def create_nodes(
        self, node_config: Dict[str, Any], count: int, tags: Tags
    ) -> Dict[NodeId, Dict]:
        # TODO: handle pending state
        created_activities = await self._golem_service.create_activities(
            node_config=node_config,
            count=count,
            ssh_user=self._ssh_user,
            ssh_private_key_path=self._ssh_private_key_path,
            ssh_public_key_path=self._ssh_public_key_path,
        )

        created_nodes = {}
        for activity, ip, ssh_proxy_command in created_activities:
            node_id = self._get_new_node_id()

            created_nodes[node_id] = Node(
                node_id=node_id,
                state=NodeState.running,
                tags=tags,
                internal_ip=ip,
                ssh_proxy_command=ssh_proxy_command,
                activity=activity,
            )

        async with self._nodes_lock:
            self._nodes.update(created_nodes)

        # TODO: Consider running tunnel on every head node
        if not self._is_head_node_to_webserver_tunnel_running():
            await self._start_head_node_to_webserver_tunnel()

        return {
            node_id: node.dict(
                exclude={
                    "activity",
                }
            )
            for node_id, node in created_nodes.items()
        }

    def _get_new_node_id(self) -> NodeId:
        node_id = f"node{self._nodes_id_counter}"
        self._nodes_id_counter += 1
        return node_id

    async def terminate_node(self, node_id: NodeId) -> Dict[NodeId, Dict]:
        async with self._get_node_context(node_id) as node:
            node.state = NodeState.stopping

        await node.activity.destroy()

        async with self._get_node_context(node_id) as node:
            del self._nodes[node.node_id]

            return {node.node_id: node.dict(exclude={"activity"})}

    async def get_non_terminated_nodes_ids(
        self, tags_to_match: Optional[Dict[str, str]] = None
    ) -> List[NodeId]:
        async with self._nodes_lock:
            if tags_to_match is None:
                return list(self._nodes.keys())

            return [
                node_id
                for node_id, node in self._nodes.items()
                if are_dicts_equal(node.tags, tags_to_match)
            ]

    async def is_node_running(self, node_id: NodeId) -> bool:
        async with self._get_node_context(node_id) as node:
            return node.state == NodeState.running

    async def is_node_terminated(self, node_id: NodeId) -> bool:
        async with self._get_node_context(node_id) as node:
            return node.state not in [NodeState.pending, NodeState.running]

    async def get_node_tags(self, node_id: NodeId) -> Dict:
        async with self._get_node_context(node_id) as node:
            return node.tags

    async def get_node_internal_ip(self, node_id: NodeId) -> str:
        async with self._get_node_context(node_id) as node:
            return node.internal_ip

    async def get_ssh_proxy_command(self, node_id: NodeId) -> str:
        async with self._get_node_context(node_id) as node:
            return node.ssh_proxy_command

    async def set_node_tags(self, node_id: NodeId, tags: Tags) -> None:
        async with self._get_node_context(node_id) as node:
            node.tags.update(tags)

    async def get_or_create_default_ssh_key(self, cluster_name: str) -> str:
        ssh_key_path = self._tmp_path / get_default_ssh_key_name(cluster_name)

        if not ssh_key_path.exists():
            ssh_key_path.parent.mkdir(parents=True, exist_ok=True)

            await run_subprocess_output(
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(ssh_key_path)
            )

            logger.info(f"Ssh key for cluster '{cluster_name}' created on path '{ssh_key_path}'")

        # TODO: async file handling
        with ssh_key_path.open("r") as f:
            return str(f.read())

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
                if node.tags.get(TAG_RAY_NODE_KIND) == NODE_KIND_HEAD:
                    return node

    def _is_head_node_to_webserver_tunnel_running(self) -> bool:
        return self._head_node_to_webserver_tunnel_process is not None

    async def _start_head_node_to_webserver_tunnel(self) -> None:
        logger.info("Starting head node to webserver tunnel...")

        head_node = await self._get_head_node()
        port = self._golem_service._ray_on_golem_port

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
        self._head_node_to_webserver_tunnel_early_exit_task = asyncio.create_task(
            self._on_head_node_to_webserver_tunnel_early_exit()
        )

        logger.info("Starting head node to webserver tunnel done")

    async def _on_head_node_to_webserver_tunnel_early_exit(self) -> None:
        await self._head_node_to_webserver_tunnel_process.communicate()

        logger.warning(f"Head node to webserver tunnel exited prematurely!")

    async def _stop_head_node_to_webserver_tunnel(self) -> None:
        process = self._head_node_to_webserver_tunnel_process

        if process is None or process.returncode is not None:
            logger.info("No need to stop head node to webserver tunnel, as it's not running")
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
