from ipaddress import IPv4Address
from typing import Dict, List

from golem_ray.server.middlewares import NodeNotFound, NodesCountExceeded, NodesNotFound, \
    DestroyActivityError
from golem_ray.server.models import CreateClusterRequestData, NodeID, NodeState, Node, ClusterNode
from golem_ray.server.services.golem.golem import GolemService


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

    async def create_cluster_on_golem(self, provider_config: CreateClusterRequestData) -> None:
        await self._golem_service.create_cluster(provider_config=provider_config)

    def get_non_terminated_nodes_ids(self, tags_to_match: Dict[str, str]) -> List[NodeID]:
        matched_ids = []
        for node_id, node in self._cluster_nodes.items():
            if self._are_dicts_equal(node.tags, tags_to_match):
                matched_ids.append(node_id)
        return matched_ids

    def is_node_running(self, node_id: NodeID) -> bool:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.state == NodeState.running
        raise NodeNotFound

    def is_node_terminated(self, node_id: NodeID) -> bool:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.state not in [NodeState.pending, NodeState.running]
        raise NodeNotFound

    def get_node_tags(self, node_id: NodeID) -> Dict:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.tags
        raise NodeNotFound

    def get_node_internal_ip(self, node_id: NodeID) -> IPv4Address:
        node = self._cluster_nodes.get(node_id)
        if node:
            return node.internal_ip
        raise NodeNotFound

    def set_node_tags(self, node_id: NodeID, tags: Dict) -> None:
        node = self._cluster_nodes.get(node_id)
        if node:
            node.tags.update(tags)
            return
        raise NodeNotFound

    async def create_nodes(self, count: int, tags: Dict) -> Dict:
        if tags is None:
            tags = {}

        if count + len(self._cluster_nodes) > self._num_workers + 1:
            raise NodesCountExceeded

        new_nodes = await self._golem_service.get_providers(tags=tags,
                                                            count=count,
                                                            current_nodes_count=len(self._cluster_nodes))
        self._cluster_nodes.update(new_nodes)

        return self._cluster_nodes

    async def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        if not all(element in node_ids for element in self._cluster_nodes.keys()):
            raise NodesNotFound(additional_message=f"Given ids: {node_ids}")
        for node_id in node_ids:
            await self._terminate_node(node_id)
            self._cluster_nodes.pop(node_id, None)

    async def _terminate_node(self, node_id: NodeID) -> None:
        node = self._cluster_nodes.get(node_id)
        if node:
            await self._golem_service.destroy_activity(node)
        raise DestroyActivityError

    @staticmethod
    def _are_dicts_equal(dict1: Dict[str, str], dict2: Dict[str, str]) -> bool:
        if set(dict1.keys()) != set(dict2.keys()):
            return False
        for key in dict1.keys():
            if dict1[key] != dict2[key]:
                return False

        return True
