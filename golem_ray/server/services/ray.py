import logging
from asyncio.subprocess import Process
from ipaddress import IPv4Address
from typing import Any, Dict, List, Optional

from golem_ray.server.exceptions import NodeNotFound, NodesNotFound
from golem_ray.server.models import CreateClusterRequestData, Node, NodeId, NodeState, Tags
from golem_ray.server.services.golem import GolemService
from golem_ray.server.services.ssh import SshService

logger = logging.getLogger(__name__)


class RayService:
    def __init__(self, golem_service: GolemService, ssh_service: SshService):
        self._golem_service = golem_service
        self._ssh_service = ssh_service

        self._nodes = {}
        self._head_node_to_webserver_tunel_process: Optional[Process] = None

    async def shutdown(self) -> None:
        await self._stop_head_node_to_webserver_tunel()

    def get_all_nodes_ids(self) -> List[NodeId]:
        return list(self._golem_service.cluster_nodes.keys())

    def get_all_nodes_dict(self) -> Dict[NodeId, Node]:
        return {
            k: Node(
                node_id=v.node_id,
                state=v.state,
                tags=v.tags,
                internal_ip=v.internal_ip,
                external_ip=v.external_ip,
            )
            for (k, v) in self._golem_service.cluster_nodes.items()
        }

    async def create_cluster_on_golem(self, provider_config: CreateClusterRequestData) -> None:
        await self._golem_service.create_cluster(provider_config=provider_config)

    def get_non_terminated_nodes_ids(self, tags_to_match: Dict[str, str]) -> List[NodeId]:
        matched_ids = []
        if not tags_to_match:
            return [node_id for node_id, node in self._golem_service.cluster_nodes.items()]

        for node_id, node in self._golem_service.cluster_nodes.items():
            if self._are_dicts_equal(node.tags, tags_to_match):
                matched_ids.append(node_id)

        return matched_ids

    def is_node_running(self, node_id: NodeId) -> bool:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            return node.state == NodeState.running
        raise NodeNotFound

    def is_node_terminated(self, node_id: NodeId) -> bool:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            return node.state not in [NodeState.pending, NodeState.running]
        raise NodeNotFound

    def get_node_tags(self, node_id: NodeId) -> Dict:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            return node.tags
        raise NodeNotFound

    def get_node_internal_ip(self, node_id: NodeId) -> IPv4Address:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            return node.internal_ip
        raise NodeNotFound

    def set_node_tags(self, node_id: NodeId, tags: Tags) -> None:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            node.tags.update(tags)
            return
        raise NodeNotFound

    async def create_nodes(self, node_config: Dict[str, Any], count: int, tags: Tags) -> Dict:
        await self._golem_service.get_providers(
            tags=tags,
            count=count,
        )

        if not self._is_head_node_to_webserver_tunel_running():
            await self._start_head_node_to_webserver_tunel()

        return self._golem_service.cluster_nodes

    def _is_head_node_to_webserver_tunel_running(self) -> bool:
        return self._head_node_to_webserver_tunel_process is not None

    async def _start_head_node_to_webserver_tunel(self) -> None:
        head_node = await self._golem_service._get_head_node()
        proxy_command = self._golem_service.get_node_ssh_proxy_command(head_node.node_id)
        private_key_path = (
            self._golem_service._temp_ssh_key_dir / self._golem_service._temp_ssh_key_filename
        )

        self._head_node_to_webserver_tunel_process = await self._ssh_service.create_ssh_reverse_tunel(
            str(head_node.internal_ip),
            self._golem_service._golem_ray_port,
            private_key_path=private_key_path,
            proxy_command=proxy_command,
        )

        # TODO: Add log when process dies early

        logger.info("Reverse tunel from remote head node to local webserver started")

    async def _stop_head_node_to_webserver_tunel(self) -> None:
        process = self._head_node_to_webserver_tunel_process

        if process is None:
            return

        if process.returncode is None:
            process.terminate()

        await process.wait()

        logger.info("Reverse tunel from remote head node to local webserver stopped")

        self._head_node_to_webserver_tunel_process = None

    async def terminate_nodes(self, node_ids: List[NodeId]) -> None:
        if not all(element in node_ids for element in self._golem_service.cluster_nodes.keys()):
            raise NodesNotFound(additional_message=f"Given ids: {node_ids}")
        for node_id in node_ids:
            await self._terminate_node(node_id)
            self._golem_service.cluster_nodes.pop(node_id, None)

    async def _terminate_node(self, node_id: NodeId) -> None:
        node = self._golem_service.cluster_nodes.get(node_id)
        if node:
            await self._golem_service.destroy_activity(node)
            return
        raise NodeNotFound

    @staticmethod
    def _are_dicts_equal(dict1: Dict[str, str], dict2: Dict[str, str]) -> bool:
        for key in dict1.keys():
            if key in dict2:
                if dict1[key] != dict2[key]:
                    return False

        return True
