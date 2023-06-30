from ipaddress import IPv4Address
from typing import Any

from ray.autoscaler._private.aws.node_provider import (
    AWSNodeProvider,
)  # testing purposes
from ray.autoscaler.node_provider import NodeProvider

from client.golem_ray_client import GolemRayClient
from models.types import NODE_ID, NodeState


class GolemNodeProvider(NodeProvider):

    def __init__(self, provider_config, cluster_name):
        super().__init__(provider_config, cluster_name)

        golem_ray_url = provider_config["parameters"]["golem_ray_url"]
        self._golem_ray_client = GolemRayClient(golem_ray_url=golem_ray_url)

        image_hash = provider_config["parameters"]["image_hash"]
        self._golem_ray_client.create_cluster(image_hash)
        # self._cluster_id = self._golem_ray_client.create_cluster(image_hash)

    def non_terminated_nodes(self, tag_filters) -> list[NODE_ID]:
        return self._golem_ray_client.non_terminated_nodes()

    def is_running(self, node_id: NODE_ID) -> bool:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.state == NodeState.running

    def is_terminated(self, node_id: NODE_ID) -> bool:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.state not in [NodeState.pending, NodeState.running]

    def node_tags(self, node_id: NODE_ID) -> dict:
        return {}
        # node = self._golem_ray_client.fetch_node(node_id)
        # return node.tags

    def external_ip(self, node_id: NODE_ID) -> IPv4Address:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.external_ip

    def internal_ip(self, node_id: NODE_ID) -> IPv4Address:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.internal_ip

    def set_node_tags(self, node_id: NODE_ID, tags: dict) -> None:
        return
        # return self._golem_ray_client.set_node_tags(node_id, tags)

    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, dict]:
        # created_nodes = self._golem_ray_client.create_nodes(cluster_id=self._cluster_id, count=count)
        created_nodes = self._golem_ray_client.create_nodes(
            cluster_id="",
            count=count,
            head_node=node_config.get("metadata", {}).get("labels", {}).get("component") == "ray-head",
        )
        return {node.node_id: node.dict() for node in created_nodes}

    def terminate_node(self, node_id: NODE_ID) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: list[NODE_ID]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)
