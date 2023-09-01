import logging
import platform
import subprocess
import sys
from ipaddress import IPv4Address
from pathlib import Path
from time import sleep
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple
from requests import ConnectionError

import ray
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider
from yarl import URL

from golem_ray.client.golem_ray_client import GolemRayClient
from golem_ray.provider.exceptions import GolemRayNodeProviderError
from golem_ray.provider.ssh_command_runner import SSHCommandRunner
from golem_ray.server.models import Node, NodeId
from golem_ray.server.settings import GOLEM_RAY_REVERSE_TUNNEL_PORT, SERVER_BASE_URL

PROJECT_ROOT = Path(__file__).parent.parent
logger = logging.getLogger()


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: dict, cluster_name: str):
        super().__init__(provider_config, cluster_name)
        self.port = provider_config["parameters"].get("webserver_port", 4578)
        self.webserver_url = f"http://localhost:{self.port}"
        self._run_webserver()
        self._golem_ray_client = GolemRayClient(base_url=URL(self.webserver_url))

        image_url, image_hash = self._get_image_url_and_hash(provider_config)
        network = provider_config["parameters"].get("network", "goerli")
        budget = provider_config["parameters"].get("budget", 1)
        self._golem_ray_client.get_running_or_create_cluster(image_url, image_hash, network, budget)
        self.ray_head_ip: Optional[str] = None

    def _run_webserver(self) -> None:
        if self._webserver_is_running():
            logger.info("Webserver is running")

        run_path = PROJECT_ROOT / "server" / "run.py"
        logger.info("Starting webserver")
        subprocess.Popen(
            [sys.executable, run_path, str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        sleep(1)
        for _ in range(3):
            if self._webserver_is_running():
                return
            logger.info("Webserver is not running yet, checking health_check again in 2 seconds")
            sleep(2)
        raise GolemRayNodeProviderError("Could not start webserver")

    def _webserver_is_running(self) -> bool:
        try:
            response = requests.get(f"{self.webserver_url}/health_check", timeout=2)
        except ConnectionError:
            return False
        else:
            return response.status_code == 200 and response.text == "ok"

    def _get_image_url_and_hash(self, provider_config: dict) -> Tuple[URL, str]:
        image_tag = provider_config["parameters"].get("image_tag")
        image_hash = provider_config["parameters"].get("image_hash")

        if image_tag is not None and image_hash is not None:
            raise GolemRayNodeProviderError(
                "Only one of 'image_tag' and 'image_hash' parameter should be defined!"
            )

        if image_hash is not None:
            image_url = self._get_image_url_from_hash(image_hash)
            return image_url, image_hash

        return self._get_image_url_and_hash_from_tag(image_tag)

    def _get_image_url_from_hash(self, image_hash: str) -> URL:
        return self._golem_ray_client.get_image_url_from_hash(image_hash)

    def _get_image_url_and_hash_from_tag(self, image_tag: Optional[str]) -> Tuple[URL, str]:
        python_version = platform.python_version()
        ray_version = ray.__version__

        if image_tag is not None:
            tag_python_version = image_tag.split("-")[0].split("py")[1]
            tag_ray_version = image_tag.split("-")[1].split("ray")[1]

            if (python_version, ray_version) != (tag_python_version, tag_ray_version):
                logging.warning(
                    "WARNING: "
                    f"Version of python and ray on your machine {(python_version, ray_version) = } "
                    f"does not match tag version {(tag_python_version, tag_ray_version) = }"
                )
        else:
            image_tag = f"py{python_version}-ray{ray_version}"

        return self._golem_ray_client.get_image_url_and_hash_from_tag(image_tag)

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
        common_args = {
            "log_prefix": log_prefix,
            "node_id": node_id,
            "provider": self,
            "auth_config": auth_config,
            "cluster_name": cluster_name,
            "process_runner": process_runner,
            "use_internal_ip": use_internal_ip,
        }

        if "ssh_proxy_command" not in auth_config:
            auth_config["ssh_proxy_command"] = self._golem_ray_client.get_ssh_proxy_command(node_id)

        return SSHCommandRunner(**common_args)

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
    ) -> Dict[NodeId, Node]:
        return self._golem_ray_client.create_nodes(
            count=count,
            tags=tags,
        )

    def terminate_node(self, node_id: NodeId) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: List[NodeId]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)

    @staticmethod
    def _is_running_on_localhost():
        return any(
            SERVER_BASE_URL.host in option for option in ["localhost", "127.0.0.1", "0.0.0.0"]
        )

    def prepare_for_head_node(self, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        """Returns a new cluster config with custom configs for head node."""
        self.ray_head_ip = self._golem_ray_client.get_head_node_ip()

        def replace_placeholders(obj):
            if isinstance(obj, str):
                obj = obj.replace(
                    "$GOLEM_RAY_REVERSE_TUNNEL_PORT", str(GOLEM_RAY_REVERSE_TUNNEL_PORT)
                )
                obj = obj.replace("$RAY_HEAD_IP", str(self.ray_head_ip))
                return obj
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: replace_placeholders(value) for key, value in obj.items()}
            else:
                return obj

        final_config = replace_placeholders(cluster_config)
        return final_config
