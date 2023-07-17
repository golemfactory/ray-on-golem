from ipaddress import IPv4Address
from typing import Any, List, Dict, Optional
from types import ModuleType

from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from golem_ray.client.golem_ray_client import GolemRayClient
from golem_ray.client.local_head_command_runner import LocalHeadCommandRunner
from models.types import NodeID, NodeState


class GolemNodeProvider(NodeProvider):

    def __init__(self, provider_config, cluster_name):
        super().__init__(provider_config, cluster_name)

        golem_ray_url = provider_config["parameters"]["golem_ray_url"]
        self._golem_ray_client = GolemRayClient(golem_ray_url=golem_ray_url)

        image_hash = provider_config["parameters"]["image_hash"]
        network = provider_config["parameters"].get("network", "goerli")
        budget = provider_config["parameters"].get("budget", 1_000)
        self._golem_ray_client.create_cluster(image_hash, network, budget)
        # self._cluster_id = self._golem_ray_client.create_cluster(image_hash)

    def get_command_runner(
        self,
        log_prefix: str,
        node_id: str,
        auth_config: Dict[str, Any],
        cluster_name: str,
        process_runner: ModuleType,
        use_internal_ip: bool,
        docker_config: Optional[Dict[str, Any]] = None,
    ) -> CommandRunnerInterface:
        return LocalHeadCommandRunner(log_prefix, cluster_name, process_runner)

    def non_terminated_nodes(self, tag_filters) -> List[NodeID]:
        node_ids = self._golem_ray_client.non_terminated_nodes()
        return [node_id for node_id in node_ids if self._tags_match(node_id, tag_filters)]

    def _tags_match(self, node_id: NodeID, tag_filters: dict) -> bool:
        node_tags = self._golem_ray_client.fetch_node(node_id).tags
        for key, value in tag_filters.items():
            if node_tags.get(key) != value:
                return False
        return True

    def is_running(self, node_id: NodeID) -> bool:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.state == NodeState.running

    def is_terminated(self, node_id: NodeID) -> bool:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.state not in [NodeState.pending, NodeState.running]

    def node_tags(self, node_id: NodeID) -> dict:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.tags

    def external_ip(self, node_id: NodeID) -> IPv4Address:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.external_ip

    def internal_ip(self, node_id: NodeID) -> IPv4Address:
        node = self._golem_ray_client.fetch_node(node_id)
        return node.internal_ip

    def set_node_tags(self, node_id: NodeID, tags: dict) -> None:
        self._golem_ray_client.set_node_tags(node_id, tags)

    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, dict]:
        # created_nodes = self._golem_ray_client.create_nodes(cluster_id=self._cluster_id, count=count)
        head_node = node_config.get("metadata", {}).get("labels", {}).get("component") == "ray-head"
        created_nodes = self._golem_ray_client.create_nodes(
            cluster_id="",
            count=count,
            tags=tags,
            head_node=head_node,
        )
        return {node.node_id: node.dict() for node in created_nodes}

    def terminate_node(self, node_id: NodeID) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)
