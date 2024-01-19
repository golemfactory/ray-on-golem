import logging
import subprocess
import time
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional

from ray.autoscaler._private.cli_logger import cli_logger
from ray.autoscaler._private.event_system import CreateClusterEvent, global_event_system
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from ray_on_golem.client.client import RayOnGolemClient
from ray_on_golem.provider.ssh_command_runner import SSHCommandRunner
from ray_on_golem.server.models import NodeData, NodeId, NodeState, ShutdownState
from ray_on_golem.server.settings import (
    LOGGING_DEBUG_PATH,
    PAYMENT_DRIVER_ERC20,
    PAYMENT_NETWORK_GOERLI,
    PAYMENT_NETWORK_MAINNET,
    PAYMENT_NETWORK_POLYGON,
    RAY_ON_GOLEM_CHECK_DEADLINE,
    RAY_ON_GOLEM_PATH,
    RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
    RAY_ON_GOLEM_START_DEADLINE,
    TMP_PATH,
)
from ray_on_golem.utils import (
    get_default_ssh_key_name,
    get_last_lines_from_file,
    is_running_on_golem_network,
    prepare_tmp_dir,
)
from ray_on_golem.version import get_version

LOG_GROUP = f"Ray On Golem {get_version()}"

ONBOARDING_MESSAGE = {
    PAYMENT_NETWORK_MAINNET: "Running Ray on Golem on the Ethereum Mainnet requires GLM and ETH tokens.",
    PAYMENT_NETWORK_POLYGON: "Running Ray on Golem on the mainnet requires GLM and MATIC tokens on the Polygon blockchain (see: https://docs.golem.network/docs/creators/ray/mainnet).",
}

PROVIDER_DEFAULTS = {
    "webserver_port": 4578,
    "enable_registry_stats": True,
    "payment_network": PAYMENT_NETWORK_GOERLI,
    "payment_driver": PAYMENT_DRIVER_ERC20,
    "subnet_tag": "public",
    "total_budget": 1.0,
}

logger = logging.getLogger(__name__)


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: Dict[str, Any], cluster_name: str):
        super().__init__(provider_config, cluster_name)

        provider_parameters: Dict = provider_config["parameters"]

        self._ray_on_golem_client = self._get_ray_on_golem_client_instance(
            provider_parameters["webserver_port"],
            provider_parameters["enable_registry_stats"],
        )

        provider_parameters = self._map_ssh_config(provider_parameters)
        self._payment_network = provider_parameters["payment_network"].lower().strip()

        cluster_creation_response = self._ray_on_golem_client.create_cluster(provider_parameters)

        self._wallet_address = cluster_creation_response.wallet_address
        self._is_cluster_just_created = cluster_creation_response.is_cluster_just_created

        self._print_mainnet_onboarding_message(
            cluster_creation_response.yagna_payment_status_output
        )

        wallet_glm_amount = float(cluster_creation_response.yagna_payment_status.get("amount", "0"))
        if not wallet_glm_amount:
            cli_logger.abort("You don't seem to have any GLM tokens on your Golem wallet.")

    @classmethod
    def bootstrap_config(cls, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        config = deepcopy(cluster_config)

        cls._apply_config_defaults(config)

        provider_parameters = config["provider"]["parameters"]
        ray_on_golem_client = cls._get_ray_on_golem_client_instance(
            provider_parameters["webserver_port"],
            provider_parameters["enable_registry_stats"],
        )
        # TODO: SAVE wallet address

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
        with cli_logger.group(LOG_GROUP):
            cli_logger.print(f"Requesting {count} nodes...")

            requested_node_ids = self._ray_on_golem_client.request_nodes(
                node_config=node_config,
                count=count,
                tags=tags,
            )

            started_at = datetime.now()
            nodes_last_log_size = {node_id: 0 for node_id in requested_node_ids}

            while True:
                cluster_state = self._ray_on_golem_client.get_cluster_state()
                monitored_nodes = {
                    node.node_id: node
                    for node in cluster_state.values()
                    if node.node_id in requested_node_ids
                }
                nodes_log_size = {
                    node.node_id: len(node.state_log) for node in monitored_nodes.values()
                }

                self._print_node_state(
                    f"Requested nodes status after {datetime.now() - started_at}",
                    monitored_nodes.values(),
                    nodes_last_log_size,
                )

                nodes_last_log_size = nodes_log_size

                if all([node.state == NodeState.running for node in monitored_nodes.values()]):
                    cli_logger.success(f"All {count} requested nodes ready")

                    return monitored_nodes

                time.sleep(5)

    def _print_node_state(
        self, group: str, nodes: Iterable[NodeData], nodes_last_log_size: Dict[NodeId, int]
    ):
        with cli_logger.group(group):
            for node in nodes:
                for i in range(nodes_last_log_size[node.node_id], len(node.state_log) - 1):
                    cli_logger.print((" " * (len(node.node_id) + 2)) + node.state_log[i])

                try:
                    log = node.state_log[-1]
                except IndexError:
                    log = "<none>"

                cli_logger.labeled_value(node.node_id, log)

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

    def internal_ip(self, node_id: NodeId) -> Optional[str]:
        return self._ray_on_golem_client.get_node_internal_ip(node_id)

    def external_ip(self, node_id: NodeId) -> Optional[str]:
        return self._ray_on_golem_client.get_node_internal_ip(node_id)

    def set_node_tags(self, node_id: NodeId, tags: Dict) -> None:
        self._ray_on_golem_client.set_node_tags(node_id, tags)

    @staticmethod
    def _map_ssh_config(provider_parameters: Dict[str, Any]):
        ssh_arg_mapping = {"_ssh_private_key": "ssh_private_key", "_ssh_user": "ssh_user"}
        return {ssh_arg_mapping.get(k) or k: v for k, v in provider_parameters.items()}

    @staticmethod
    def _apply_config_defaults(config: Dict[str, Any]) -> None:
        provider_parameters: Dict = config["provider"]["parameters"]
        for k, v in PROVIDER_DEFAULTS.items():
            provider_parameters.setdefault(k, v)

        auth: Dict = config.setdefault("auth", {})
        auth.setdefault("ssh_user", "root")

        if "ssh_private_key" not in auth:
            auth["ssh_private_key"] = str(
                TMP_PATH / get_default_ssh_key_name(config["cluster_name"])
            )

        # copy ssh details to provider namespace for cluster creation in __init__
        provider_parameters["_ssh_private_key"] = auth["ssh_private_key"]
        provider_parameters["_ssh_user"] = auth["ssh_user"]

    @classmethod
    def _start_webserver(
        cls,
        ray_on_golem_client: RayOnGolemClient,
        port: int,
        registry_stats: bool,
    ) -> None:
        with cli_logger.group(LOG_GROUP):
            webserver_serviceable = ray_on_golem_client.is_webserver_serviceable()
            if webserver_serviceable:
                cli_logger.print("Not starting webserver, as it's already running")
                return
            elif webserver_serviceable is False:
                cls._wait_for_shutdown(ray_on_golem_client)

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

            log_file_path = LOGGING_DEBUG_PATH
            prepare_tmp_dir()
            log_file = log_file_path.open("w")
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
                    if ray_on_golem_client.is_webserver_serviceable():
                        cli_logger.print("Starting webserver done")
                        return
                else:
                    cli_logger.abort(
                        "Starting webserver failed!\nShowing last 50 lines from `{}`:\n{}",
                        log_file_path,
                        get_last_lines_from_file(log_file_path, 50),
                    )

                cli_logger.print(
                    "Webserver is not yet running, waiting additional `{}` seconds...",
                    check_seconds,
                )

            cli_logger.abort(
                "Starting webserver failed! Deadline of `{}` reached.\nShowing last 50 lines from `{}`:\n{}",
                RAY_ON_GOLEM_START_DEADLINE,
                log_file_path,
                get_last_lines_from_file(log_file_path, 50),
            )

    @staticmethod
    def _stop_webserver(ray_on_golem_client: RayOnGolemClient) -> None:
        with cli_logger.group(LOG_GROUP):
            webserver_serviceable = ray_on_golem_client.is_webserver_serviceable()
            if not webserver_serviceable:
                if webserver_serviceable is None:
                    cli_logger.print("Not stopping the webserver, as it's not running")
                else:
                    cli_logger.print("Not stopping the webserver, as it's already shutting down")

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

    @staticmethod
    def _wait_for_shutdown(ray_on_golem_client: RayOnGolemClient) -> None:
        cli_logger.print(
            "Previous webserver instance is still shutting down, waiting with deadline up to `{}`...",
            RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
        )

        wait_deadline = datetime.now() + RAY_ON_GOLEM_SHUTDOWN_DEADLINE
        check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())

        time.sleep(check_seconds)
        while datetime.now() < wait_deadline:
            webserver_serviceable = ray_on_golem_client.is_webserver_serviceable()
            if webserver_serviceable is None:
                cli_logger.print("Previous webserver instance shutdown done")
                return

            cli_logger.print(
                "Previous webserver instance is not yet shutdown, waiting additional `{}` seconds...",
                check_seconds,
            )
            time.sleep(check_seconds)

        cli_logger.abort(
            "Previous webserver instance is still running! Deadline of `{}` reached.",
            RAY_ON_GOLEM_START_DEADLINE,
        )

    def _print_mainnet_onboarding_message(self, yagna_payment_status_output: str) -> None:
        if self._payment_network not in ONBOARDING_MESSAGE:
            return

        cli_logger.newline()

        with cli_logger.indented():
            cli_logger.print(ONBOARDING_MESSAGE.get(self._payment_network))
            cli_logger.print("Your wallet:")

            with cli_logger.indented():
                for line in yagna_payment_status_output.splitlines():
                    cli_logger.print(line)

            cli_logger.newline()
            cli_logger.print(
                "You can use the Golem Onboarding portal to top up: https://golemfactory.github.io"
                f"/onboarding_production/?yagnaAddress={self._wallet_address}"
                "\n\n"
                "DISCLAIMER: Please keep in mind that in its current stage, the Onboarding Portal "
                "is an EXPERIMENTAL product. Even though it is functional, "
                "we do not recommend using it unless you wish to help us beta-test this feature. "
                "You'll find more information on `#Payment UX` discord channel "
                "https://discord.com/channels/684703559954333727/1136984764197380096"
            )
            cli_logger.newline()
