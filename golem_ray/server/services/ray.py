from ipaddress import IPv4Address
from typing import Dict, List

from golem_ray.server.middlewares.error_handling import RayException
from golem_ray.server.models.cluster_node import ClusterNode
from golem_ray.server.services.golem import GolemService
from models.types import NodeID, NodeState, Node


class RayService:

    def __init__(self, golem_service: GolemService):
        self._golem_service = golem_service
        self._cluster_nodes: Dict[int, ClusterNode] = {}
        self._num_workers = 2

    def get_all_nodes_ids(self) -> List[NodeID]:
        return list(self._cluster_nodes.keys())

    def get_all_nodes_dict(self) -> Dict:
        return {k: Node(
            node_id=v.node_id,
            state=v.state,
            tags=v.tags,
            internal_ip=v.internal_ip,
            external_ip=v.external_ip
        )
            for (k, v) in self._cluster_nodes.items()}

    def get_non_terminated_nodes_ids(self, tags_to_match: Dict[str, str]) -> List[NodeID]:
        matched_ids = []
        for node_id, node in self._cluster_nodes.items():
            if node.tags == tags_to_match:
                matched_ids.append(node_id)
        return matched_ids

    def is_node_running(self, node_id: NodeID) -> bool:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.state == NodeState.running
        raise RayException(message=RayException.NODE_NOT_FOUND)

    def is_node_terminated(self, node_id: NodeID) -> bool:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.state not in [NodeState.pending, NodeState.running]
        raise RayException(message=RayException.NODE_NOT_FOUND)

    def get_node_tags(self, node_id: NodeID) -> Dict:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.tags
        raise RayException(message=RayException.NODE_NOT_FOUND)

    def get_node_internal_ip(self, node_id: NodeID) -> IPv4Address:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.internal_ip
        raise RayException(message=RayException.NODE_NOT_FOUND)

    def set_node_tags(self, node_id: NodeID, tags: Dict) -> None:
        node = self._cluster_nodes.get(node_id)
        if node:
            node.tags.update(tags)
            return
        raise RayException(message=RayException.NODE_NOT_FOUND)

    async def create_nodes(self, count: int, tags: Dict) -> Dict:
        if tags is None:
            tags = {}

        if count + len(self._cluster_nodes) > self._num_workers + 1:
            raise RayException(message=RayException.NODES_COUNT_EXCEEDED)

        new_nodes = await self._golem_service.get_providers(tags=tags,
                                                            count=count,
                                                            current_nodes_count=len(self._cluster_nodes))
        self._cluster_nodes.update(new_nodes)

        return self._cluster_nodes

    async def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        if not all(element in node_ids for element in self._cluster_nodes.keys()):
            raise RayException(message=RayException.NODES_NOT_FOUND, additional_message=f"Given ids: {node_ids}")
        for node_id in node_ids:
            await self._terminate_single_node(node_id)
            self._cluster_nodes.pop(node_id, None)

    async def _terminate_single_node(self, node_id: NodeID) -> None:
        node = self._cluster_nodes.get(node_id)
        if node:
            try:
                await node.activity.destroy()
            except Exception:
                raise RayException(message=RayException.DESTROY_ACTIVITY_ERROR, additional_message=f"Node_id={node_id}")
