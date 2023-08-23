from ipaddress import IPv4Address
from typing import Dict, List

from golem_ray.server.exceptions import (
    DestroyActivityError,
    NodeNotFound,
    NodesCountExceeded,
    NodesNotFound,
)
from golem_ray.server.models import CreateClusterRequestData, Node, NodeId, NodeState, Tags
from golem_ray.server.services import GolemService


class RayService:
    def __init__(self, golem_service: GolemService):
        self._golem_service = golem_service
        self._num_workers = 15

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
        print('tags_to_match: ', tags_to_match)
        if not tags_to_match:
            return [node_id for node_id, node in self._golem_service.cluster_nodes.items()]

        for node_id, node in self._golem_service.cluster_nodes.items():
            print(node_id, ': ', node.tags)
            if self._are_dicts_equal(node.tags, tags_to_match):
                matched_ids.append(node_id)

        print('non_terminated_nodes_ids: ', matched_ids)
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

    async def create_nodes(self, count: int, tags: Tags) -> Dict:
        if tags is None:
            tags = {}

        if count + len(self._golem_service.cluster_nodes) > self._num_workers + 1:
            raise NodesCountExceeded

        await self._golem_service.get_providers(tags=tags, count=count,)

        return self._golem_service.cluster_nodes

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
        raise DestroyActivityError

    @staticmethod
    def _are_dicts_equal(dict1: Dict[str, str], dict2: Dict[str, str]) -> bool:
        for key in dict1.keys():
            if key in dict2:
                if dict1[key] != dict2[key]:
                    return False
            # if dict1[key] != dict2[key]:
            #     return False

        return True

    async def get_node_ssh_port(self, node_id: NodeId) -> int:
        return self._golem_service.get_node_ssh_port(node_id)
