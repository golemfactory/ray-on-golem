from ipaddress import IPv4Address
from typing import Any

from ray.autoscaler._private.aws.node_provider import (
    AWSNodeProvider,
)  # testing purposes
from ray.autoscaler.node_provider import NodeProvider

from client.golem_ray_client import GolemRayClient
from models.types import NODE_ID


class GolemNodeProvider(NodeProvider):

    def __init__(self, provider_config, cluster_name):
        super().__init__(provider_config, cluster_name)

        self.golem_ray_client = GolemRayClient(
            golem_ray_url=provider_config["parameters"]["golem_ray_url"],
        )
        self._cluster_id = self.golem_ray_client.create_cluster()

    def non_terminated_nodes(self, tag_filters) -> list[NODE_ID]:
        return self.golem_ray_client.non_terminated_nodes()

    def is_running(self, node_id: NODE_ID) -> bool:
        return self.golem_ray_client.is_running(node_id)

    def is_terminated(self, node_id: NODE_ID) -> bool:
        return self.golem_ray_client.is_terminated(node_id)

    def node_tags(self, node_id: NODE_ID):
        ...

    def external_ip(self, node_id: NODE_ID) -> IPv4Address:
        return self.golem_ray_client.external_ip(node_id)

    def internal_ip(self, node_id: NODE_ID) -> IPv4Address:
        return self.golem_ray_client.internal_ip(node_id)

    def set_node_tags(self, node_id, tags):
        ...

    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, dict]:
        created_nodes = self.golem_ray_client.create_nodes(cluster_id=self._cluster_id, count=count)
        return {node.node_id: node.dict() for node in created_nodes}

    def terminate_node(self, node_id: NODE_ID) -> None:
        return self.golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: list[NODE_ID]) -> None:
        return self.golem_ray_client.terminate_nodes(node_ids)
