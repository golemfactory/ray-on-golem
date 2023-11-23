import logging
import subprocess
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from types import ModuleType
from typing import Any, Dict, List, Optional

from ray.autoscaler._private.cli_logger import cli_logger
from ray.autoscaler._private.event_system import CreateClusterEvent, global_event_system
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from ray_on_golem.client.client import RayOnGolemClient
from ray_on_golem.provider.ssh_command_runner import SSHCommandRunner
from ray_on_golem.server.models import NodeConfigData, NodeId, ShutdownState
from ray_on_golem.server.settings import (
    LOGGING_DEBUG_PATH,
    RAY_ON_GOLEM_CHECK_DEADLINE,
    RAY_ON_GOLEM_PATH,
    RAY_ON_GOLEM_START_DEADLINE,
    TMP_PATH,
)
from ray_on_golem.utils import (
    get_default_ssh_key_name,
    get_last_lines_from_file,
    is_running_on_golem_network,
    prepare_tmp_dir,
)

logger = logging.getLogger(__name__)
WEBSERVER_LOG_GROUP = "Ray On Golem webserver"

WEBSERVER_OUTFILE = TMP_PATH / "webserver.out"
WEBSERVER_ERRFILE = TMP_PATH / "webserver.err"


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: dict, cluster_name: str):
        super().__init__(provider_config, cluster_name)

        provider_parameters = provider_config["parameters"]

        self._ray_on_golem_client = self._get_ray_on_golem_client_instance(
            provider_parameters["webserver_port"],
            provider_parameters["enable_registry_stats"],
        )
        self._ray_on_golem_client.create_cluster(
            network=provider_parameters["network"],
            budget_limit=provider_parameters["budget_limit"],
            node_config=NodeConfigData(**(provider_parameters.get("node_config") or {})),
            ssh_private_key=provider_parameters["_ssh_private_key"],
            ssh_user=provider_parameters["_ssh_user"],
        )

    @classmethod
    def bootstrap_config(cls, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        config = deepcopy(cluster_config)

        cls._apply_config_defaults(config)

        provider_parameters = config["provider"]["parameters"]
        ray_on_golem_client = cls._get_ray_on_golem_client_instance(
            provider_parameters["webserver_port"],
            provider_parameters["enable_registry_stats"],
        )

        auth = config["auth"]
        default_ssh_private_key = TMP_PATH / get_default_ssh_key_name(config["cluster_name"])
        if auth["ssh_private_key"] == str(default_ssh_private_key):
            if not default_ssh_private_key.exists():
                ssh_key_base64 = ray_on_golem_client.get_or_create_default_ssh_key(
                    config["cluster_name"]
                )

                # FIXME: mitigate double file writing on local machine as get_or_create_default_ssh_key creates the file
                default_ssh_private_key.parent.mkdir(parents=True, exist_ok=True)
                with default_ssh_private_key.open("w") as f:
                    f.write(ssh_key_base64)

        global_event_system.execute_callback(
            CreateClusterEvent.ssh_keypair_downloaded,
            {"ssh_key_path": auth["ssh_private_key"]},
        )

        return config

    @classmethod
    @lru_cache()
    def _get_ray_on_golem_client_instance(cls, webserver_port: int, enable_registry_stats: bool):
        ray_on_golem_client = RayOnGolemClient(webserver_port)

        if not is_running_on_golem_network():
            cls._start_webserver(ray_on_golem_client, webserver_port, enable_registry_stats)

        return ray_on_golem_client

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

        if "ssh_proxy_command" not in auth_config and not is_running_on_golem_network():
            auth_config["ssh_proxy_command"] = self._ray_on_golem_client.get_ssh_proxy_command(
                node_id
            )

        return SSHCommandRunner(**common_args)

    def create_node(
        self,
        node_config: Dict[str, Any],
        tags: Dict[str, str],
        count: int,
    ) -> Dict[NodeId, Dict]:
        return self._ray_on_golem_client.create_nodes(
            node_config=node_config,
            count=count,
            tags=tags,
        )

    def terminate_node(self, node_id: NodeId) -> Dict[NodeId, Dict]:
        terminated_nodes = self._ray_on_golem_client.terminate_node(node_id)

        self._stop_webserver(self._ray_on_golem_client)

        return terminated_nodes

    def non_terminated_nodes(self, tag_filters) -> List[NodeId]:
        return self._ray_on_golem_client.non_terminated_nodes(tag_filters)

    def is_running(self, node_id: NodeId) -> bool:
        return self._ray_on_golem_client.is_running(node_id)

    def is_terminated(self, node_id: NodeId) -> bool:
        return self._ray_on_golem_client.is_terminated(node_id)

    def node_tags(self, node_id: NodeId) -> Dict:
        return self._ray_on_golem_client.get_node_tags(node_id)

    def internal_ip(self, node_id: NodeId) -> str:
        return self._ray_on_golem_client.get_node_internal_ip(node_id)

    def external_ip(self, node_id: NodeId) -> str:
        return self._ray_on_golem_client.get_node_internal_ip(node_id)

    def set_node_tags(self, node_id: NodeId, tags: Dict) -> None:
        self._ray_on_golem_client.set_node_tags(node_id, tags)

    @staticmethod
    def _apply_config_defaults(config: Dict[str, Any]) -> None:
        provider_parameters: Dict = config["provider"]["parameters"]
        provider_parameters.setdefault("webserver_port", 4578)
        provider_parameters.setdefault("enable_registry_stats", True)
        provider_parameters.setdefault("network", "goerli")
        provider_parameters.setdefault("budget_limit", 1)

        auth: Dict = config.setdefault("auth", {})
        auth.setdefault("ssh_user", "root")

        if "ssh_private_key" not in auth:
            auth["ssh_private_key"] = str(
                TMP_PATH / get_default_ssh_key_name(config["cluster_name"])
            )

        # copy ssh details to provider namespace for cluster creation in __init__
        provider_parameters["_ssh_private_key"] = auth["ssh_private_key"]
        provider_parameters["_ssh_user"] = auth["ssh_user"]

    @staticmethod
    def _start_webserver(
        ray_on_golem_client: RayOnGolemClient,
        port: int,
        registry_stats: bool,
    ) -> None:
        with cli_logger.group(WEBSERVER_LOG_GROUP):
            if ray_on_golem_client.is_webserver_running():
                cli_logger.print("Not starting webserver, as it's already running")
                return

            cli_logger.print(
                "Starting webserver with deadline up to `{}`...", RAY_ON_GOLEM_START_DEADLINE
            )
            args = [
                RAY_ON_GOLEM_PATH,
                "webserver",
                "-p",
                str(port),
                "--registry-stats" if registry_stats else "--no-registry-stats",
                "--self-shutdown",
            ]

            cli_logger.verbose("Webserver command: `{}`", " ".join([str(a) for a in args]))

            prepare_tmp_dir()
            log_file = LOGGING_DEBUG_PATH.open("w")
            proc = subprocess.Popen(
                args,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )

            start_deadline = datetime.now() + RAY_ON_GOLEM_START_DEADLINE
            check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())
            while datetime.now() < start_deadline:
                try:
                    proc.communicate(timeout=check_seconds)
                except subprocess.TimeoutExpired:
                    if ray_on_golem_client.is_webserver_running():
                        cli_logger.print("Starting webserver done")
                        return
                else:
                    cli_logger.abort(
                        "Starting webserver failed!\nShowing last 50 lines from `{}`:\n{}",
                        LOGGING_DEBUG_PATH,
                        get_last_lines_from_file(LOGGING_DEBUG_PATH, 50),
                    )

                cli_logger.print(
                    "Webserver is not yet running, waiting additional `{}` seconds...",
                    check_seconds,
                )

            cli_logger.abort(
                "Starting webserver failed! Deadline of `{}` reached.\nShowing last 50 lines from `{}`:\n{}",
                RAY_ON_GOLEM_START_DEADLINE,
                LOGGING_DEBUG_PATH,
                get_last_lines_from_file(LOGGING_DEBUG_PATH, 50),
            )

    @staticmethod
    def _stop_webserver(ray_on_golem_client: RayOnGolemClient) -> None:
        with cli_logger.group(WEBSERVER_LOG_GROUP):
            if not ray_on_golem_client.is_webserver_running():
                cli_logger.print("Not stopping webserver, as it's already not running")
                return

            cli_logger.print("Requesting webserver shutdown...")

            shutdown_state = ray_on_golem_client.shutdown_webserver()

            if shutdown_state == ShutdownState.NOT_ENABLED:
                cli_logger.print("Not stopping webserver, as it was started externally")
                return
            elif shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
                cli_logger.print("Not stopping webserver, as the cluster is not empty")
                return

            cli_logger.print("Requesting webserver shutdown done, will stop soon")
