import logging
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from time import sleep
from types import ModuleType
from typing import Any, Dict, List, Optional

import requests
from ray.autoscaler._private.event_system import CreateClusterEvent, global_event_system
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider
from requests import ConnectionError

from golem_ray.provider.exceptions import GolemRayNodeProviderError
from golem_ray.provider.ssh_command_runner import SSHCommandRunner
from golem_ray.server.models import Node, NodeConfigData, NodeId
from golem_ray.server.settings import GOLEM_RAY_PORT, TMP_PATH, URL_HEALTH_CHECK
from golem_ray.utils import get_golem_ray_client, get_ssh_key_name

PROJECT_ROOT = Path(__file__).parent.parent
logger = logging.getLogger(__name__)


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: dict, cluster_name: str):
        super().__init__(provider_config, cluster_name)

        provider_parameters = provider_config["parameters"]

        # FIXME: Enable autostart webserver
        # self._run_webserver()
        self.ray_head_ip: Optional[str] = None

        node_config = provider_parameters["node_config"]

        self._golem_ray_client = get_golem_ray_client(provider_parameters["webserver_port"])
        self._golem_ray_client.get_running_or_create_cluster(
            cluster_name=cluster_name,
            network=provider_parameters["network"],
            budget=provider_parameters["budget"],
            node_config=NodeConfigData(**node_config),
        )

    @staticmethod
    def bootstrap_config(cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        config = deepcopy(cluster_config)

        provider_parameters: Dict = config["provider"]["parameters"]
        provider_parameters.setdefault("webserver_port", GOLEM_RAY_PORT)
        provider_parameters.setdefault("network", "goerli")
        provider_parameters.setdefault("budget", 1)

        golem_ray_client = get_golem_ray_client(provider_parameters["webserver_port"])

        auth: Dict = config["auth"]
        if "ssh_private_key" not in auth:
            ssh_key_path = TMP_PATH / get_ssh_key_name(config["cluster_name"])
            auth["ssh_private_key"] = str(ssh_key_path)

            if not ssh_key_path.exists():
                ssh_key_base64 = golem_ray_client.get_or_create_ssh_key(config["cluster_name"])
                ssh_key_path.parent.mkdir(parents=True, exist_ok=True)
                with ssh_key_path.open("w") as f:
                    f.write(ssh_key_base64)

        global_event_system.execute_callback(
            CreateClusterEvent.ssh_keypair_downloaded,
            {"ssh_key_path": config["auth"]["ssh_private_key"]},
        )

        return config

    def _run_webserver(self) -> None:
        if self._webserver_is_running():
            logger.info("Webserver is already running")
            return

        run_path = PROJECT_ROOT / "server" / "run.py"
        logger.info("Starting webserver...")
        subprocess.Popen(
            [sys.executable, run_path, str(self.provider_config["parameters"]["webserver_port"])],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        sleep(2)

        for _ in range(3):
            if self._webserver_is_running():
                logger.info("Webserver started")
                return

            logger.info("Webserver is not yet running, retrying in 2 seconds...")
            sleep(2)

        raise GolemRayNodeProviderError("Could not start webserver")

    def _webserver_is_running(self) -> bool:
        try:
            response = requests.get(self._webserver_url / URL_HEALTH_CHECK.lstrip("/"), timeout=2)
        except ConnectionError:
            return False
        else:
            return response.status_code == 200 and response.text == "ok"

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

        if "ssh_proxy_command" not in auth_config and not self._is_running_on_golem_network():
            auth_config["ssh_proxy_command"] = self._golem_ray_client.get_ssh_proxy_command(node_id)

        return SSHCommandRunner(**common_args)

    @staticmethod
    def _is_running_on_golem_network() -> bool:
        return os.getenv("ON_GOLEM_NETWORK") is not None

    def non_terminated_nodes(self, tag_filters) -> List[NodeId]:
        return self._golem_ray_client.non_terminated_nodes(tag_filters)

    def is_running(self, node_id: NodeId) -> bool:
        return self._golem_ray_client.is_running(node_id)

    def is_terminated(self, node_id: NodeId) -> bool:
        return self._golem_ray_client.is_terminated(node_id)

    def node_tags(self, node_id: NodeId) -> Dict:
        return self._golem_ray_client.get_node_tags(node_id)

    def internal_ip(self, node_id: NodeId) -> str:
        return self._golem_ray_client.get_node_internal_ip(node_id)

    def external_ip(self, node_id: NodeId) -> str:
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
            node_config=node_config,
            count=count,
            tags=tags,
        )

    def terminate_node(self, node_id: NodeId) -> None:
        return self._golem_ray_client.terminate_node(node_id)

    def terminate_nodes(self, node_ids: List[NodeId]) -> None:
        return self._golem_ray_client.terminate_nodes(node_ids)
