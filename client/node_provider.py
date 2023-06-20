from typing import Any

from ray.autoscaler._private.aws.node_provider import (
    AWSNodeProvider,
)  # testing purposes
from ray.autoscaler.node_provider import NodeProvider

from golem_ray_client import GolemRayClient
from start_ray_cluster import create_ssh_connection


class GolemNodeProvider(NodeProvider):

    def __init__(self, provider_config, cluster_name):
        super().__init__(provider_config, cluster_name)

        self.golem_ray_client = GolemRayClient(
            golem_ray_url=provider_config["golem_ray_url"],
        )
        self._cluster_id = self.golem_ray_client.create_cluster()

    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, dict]:
        created_nodes = self.golem_ray_client.create_nodes(cluster_id=self._cluster_id, count=count)
        return {node.node_id: node.dict() for node in created_nodes}
