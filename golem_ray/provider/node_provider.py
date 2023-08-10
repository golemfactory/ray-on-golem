from ipaddress import IPv4Address
from types import ModuleType
from typing import Any, List, Dict, Optional

from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from golem_ray.client.golem_ray_client import GolemRayClient
from golem_ray.provider.ssh_command_runner import SSHProviderCommandRunner
from golem_ray.server.config import BASE_URL
from golem_ray.server.models import NodeID


class GolemNodeProvider(NodeProvider):

    def __init__(self, provider_config: dict, cluster_name: str):
        super().__init__(provider_config, cluster_name)
        self._golem_ray_client = GolemRayClient(base_url=BASE_URL)

        image_hash = provider_config["parameters"]["image_hash"]
        network = provider_config["parameters"].get("network", "goerli")
        budget = provider_config["parameters"].get("budget", 100)
        self._golem_ray_client.get_running_or_create_cluster(image_hash, network, budget)

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
        node_port = self._golem_ray_client.get_node_port(node_id)
        command_runner = SSHProviderCommandRunner(log_prefix,
                                                  node_id,
                                                  self,
                                                  auth_config,
                                                  cluster_name,
                                                  process_runner,
                                                  True)
        command_runner.set_ssh_port(node_port)

        return command_runner

    def non_terminated_nodes(self, tag_filters) -> List[NodeID]:
        return self._golem_ray_client.non_terminated_nodes(tag_filters)

    def is_running(self, node_id: NodeID) -> bool:
        return self._golem_ray_client.is_running(node_id)

    def is_terminated(self, node_id: NodeID) -> bool:
        return self._golem_ray_client.is_terminated(node_id)

    def node_tags(self, node_id: NodeID) -> Dict:
        return self._golem_ray_client.get_node_tags(node_id)

    def internal_ip(self, node_id: NodeID) -> IPv4Address:
        return self._golem_ray_client.get_node_internal_ip(node_id)

    def set_node_tags(self, node_id: NodeID, tags: Dict) -> None:
        self._golem_ray_client.set_node_tags(node_id, tags)

    def create_node(
            self,
            node_config: Dict[str, Any],
            tags: Dict[str, str],
            count: int,
    ) -> Dict[str, Dict]:
        return self._golem_ray_client.create_nodes(
            cluster_id="",
            count=count,
            tags=tags,
        )

    def terminate_node(self, node_id: NodeID) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)
