import platform
from ipaddress import IPv4Address
from types import ModuleType
from typing import Any, Dict, List, Optional

import ray
import requests
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from golem_ray.client.golem_ray_client import GolemRayClient
from golem_ray.provider.exceptions import GolemRayNodeProviderError
from golem_ray.provider.local_head_command_runner import LocalHeadCommandRunner
from golem_ray.server.models import NodeId
from golem_ray.server.settings import SERVER_BASE_URL


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: dict, cluster_name: str):
        super().__init__(provider_config, cluster_name)
        self._golem_ray_client = GolemRayClient(base_url=SERVER_BASE_URL)

        image_hash = self._get_image_hash(provider_config)
        network = provider_config["parameters"].get("network", "goerli")
        budget = provider_config["parameters"].get("budget", 1)
        self._golem_ray_client.get_running_or_create_cluster(image_hash, network, budget)

    @staticmethod
    def _get_image_hash(provider_config: dict) -> str:
        python_version = platform.python_version()
        ray_version = ray.__version__
        if "image_tag" in provider_config["parameters"]:
            image_tag = provider_config["parameters"]["image_tag"]
            tag_python_version = image_tag.split("-")[0].split("py")[1]
            tag_ray_version = image_tag.split("-")[1].split("ray")[1]
            if (python_version, ray_version) != (tag_python_version, tag_ray_version):
                print(
                    "WARNING: "
                    f"Version of python and ray on your machine {(python_version, ray_version)=}"
                    f" does not match tag version {(tag_python_version, tag_ray_version)=}"
                )
        else:
            image_tag = f"py{python_version}-ray{ray_version}"

        response = requests.get(
            f"https://registry.golem.network/v1/image/info?tag=loop/golem-ray:{image_tag}",
        )
        if response.status_code == 200:
            return response.json()["sha3"]
        raise GolemRayNodeProviderError(f"Image tag {image_tag } does not exist")

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

    def non_terminated_nodes(self, tag_filters) -> List[NodeId]:
        return self._golem_ray_client.non_terminated_nodes(tag_filters)

    def is_running(self, node_id: NodeId) -> bool:
        return self._golem_ray_client.is_running(node_id)

    def is_terminated(self, node_id: NodeId) -> bool:
        return self._golem_ray_client.is_terminated(node_id)

    def node_tags(self, node_id: NodeId) -> Dict:
        return self._golem_ray_client.get_node_tags(node_id)

    def internal_ip(self, node_id: NodeId) -> IPv4Address:
        return self._golem_ray_client.get_node_internal_ip(node_id)

    def set_node_tags(self, node_id: NodeId, tags: Dict) -> None:
        self._golem_ray_client.set_node_tags(node_id, tags)

    def create_node(
        self,
        node_config: Dict[str, Any],
        tags: Dict[str, str],
        count: int,
    ) -> Dict[str, Dict]:
        return self._golem_ray_client.create_nodes(
            count=count,
            tags=tags,
        )

    def terminate_node(self, node_id: NodeId) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: List[NodeId]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)
