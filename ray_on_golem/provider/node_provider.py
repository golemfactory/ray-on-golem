import os
import time
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional

import dpath.util
from ray.autoscaler._private.cli_logger import cli_logger
from ray.autoscaler._private.event_system import CreateClusterEvent, global_event_system
from ray.autoscaler.command_runner import CommandRunnerInterface
from ray.autoscaler.node_provider import NodeProvider

from ray_on_golem.client import RayOnGolemClient
from ray_on_golem.ctl import RayOnGolemCtl
from ray_on_golem.provider.log import NodeProviderCliLogger
from ray_on_golem.provider.ssh_command_runner import SSHCommandRunner
from ray_on_golem.server.models import NodeData, NodeId, NodeState
from ray_on_golem.server.settings import (
    PAYMENT_DRIVER_ERC20,
    PAYMENT_NETWORK_GOERLI,
    PAYMENT_NETWORK_MAINNET,
    PAYMENT_NETWORK_POLYGON,
    TMP_PATH,
)
from ray_on_golem.utils import get_default_ssh_key_name, is_running_on_golem_network
from ray_on_golem.version import get_version

LOG_GROUP = f"Ray On Golem {get_version()}"


ONBOARDING_MESSAGE = {
    PAYMENT_NETWORK_MAINNET: "Running Ray on Golem on the Ethereum Mainnet requires GLM and ETH tokens.",
    PAYMENT_NETWORK_POLYGON: "Running Ray on Golem on the mainnet requires GLM and MATIC tokens "
    "on the Polygon blockchain (see: https://docs.golem.network/docs/creators/ray/mainnet).",
}

PROVIDER_DEFAULTS = {
    "webserver_port": 4578,
    "webserver_datadir": None,
    "enable_registry_stats": True,
    "payment_network": PAYMENT_NETWORK_GOERLI,
    "payment_driver": PAYMENT_DRIVER_ERC20,
    "node_config": {
        "subnet_tag": "public",
        "priority_head_subnet_tag": "ray-on-golem-heads",
    },
    "total_budget": 1.0,
}


class GolemNodeProvider(NodeProvider):
    def __init__(self, provider_config: Dict[str, Any], cluster_name: str):
        super().__init__(provider_config, cluster_name)

        provider_parameters: Dict = provider_config["parameters"]

        self._ray_on_golem_client = self._ensure_webserver_and_get_client(
            port=provider_parameters["webserver_port"],
            registry_stats=provider_parameters["enable_registry_stats"],
            datadir=provider_parameters["webserver_datadir"],
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

    @staticmethod
    def fillout_available_node_types_resources(cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        cluster_config.pop("head_node", None)
        cluster_config.pop("worker_nodes", None)

        return cluster_config

    @classmethod
    @lru_cache()
    def _ensure_webserver_and_get_client(
        cls,
        port: int,
        registry_stats: bool = True,
        datadir: Optional[str] = None,
    ) -> RayOnGolemClient:
        if datadir:
            datadir = Path(datadir)

        client = RayOnGolemClient(port)
        ctl = RayOnGolemCtl(client=client, output_logger=NodeProviderCliLogger(), datadir=datadir)

        # consider starting the webserver only if this code is executed
        # on a requestor agent and not inside the VM on a provider
        if not is_running_on_golem_network():
            with cli_logger.group(LOG_GROUP):
                ctl.start_webserver(registry_stats, self_shutdown=True)

        return client

    @classmethod
    def bootstrap_config(cls, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        config = deepcopy(cluster_config)

        cls._apply_config_defaults(config)

        provider_parameters = config["provider"]["parameters"]
        ray_on_golem_client = cls._ensure_webserver_and_get_client(
            port=provider_parameters["webserver_port"],
            registry_stats=provider_parameters["enable_registry_stats"],
            datadir=provider_parameters["webserver_datadir"],
        )
        # TODO: SAVE wallet address

        auth = config["auth"]
        default_ssh_private_key = TMP_PATH / get_default_ssh_key_name(config["cluster_name"])
        if auth["ssh_private_key"] == str(default_ssh_private_key):
            if not default_ssh_private_key.exists():
                priv_base64, pub_base64 = ray_on_golem_client.get_or_create_default_ssh_key(
                    config["cluster_name"]
                )

                default_ssh_private_key.parent.mkdir(parents=True, exist_ok=True)
                pub_key_path = default_ssh_private_key.with_suffix(".pub")
                with default_ssh_private_key.open("w") as f:
                    f.write(priv_base64)

                os.chmod(default_ssh_private_key, 0o600)

                with pub_key_path.open("w") as f:
                    f.write(pub_base64)

        global_event_system.execute_callback(
            CreateClusterEvent.ssh_keypair_downloaded,
            {"ssh_key_path": auth["ssh_private_key"]},
        )

        return config

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
                elif all([node.state == NodeState.terminated for node in monitored_nodes.values()]):
                    cli_logger.abort("All node requests failed!")

                    return {}
                elif any([node.state == NodeState.terminated for node in monitored_nodes.values()]):
                    cli_logger.warning("Some node requests failed!")

                    return monitored_nodes

                time.sleep(5)

    def _print_node_state(
        self, group: str, nodes: Iterable[NodeData], nodes_last_log_size: Dict[NodeId, int]
    ):
        with cli_logger.group(group):
            for node in nodes:
                for i in range(nodes_last_log_size[node.node_id], len(node.state_log) - 1):
                    cli_logger.print(
                        (" " * (len(node.node_id) + 2)) + node.state_log[i],
                        no_format=True,
                    )

                try:
                    log = node.state_log[-1]
                except IndexError:
                    log = "<none>"

                cli_logger.labeled_value(node.node_id, log, no_format=True)

    def terminate_node(self, node_id: NodeId) -> Dict[NodeId, Dict]:
        return self._ray_on_golem_client.terminate_node(node_id)

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
        provider_parameters: Dict = deepcopy(PROVIDER_DEFAULTS)

        dpath.util.merge(
            provider_parameters,
            config["provider"]["parameters"],
        )

        config["provider"]["parameters"] = provider_parameters

        for node_type in config.get("available_node_types", {}).values():
            node_config = deepcopy(config["provider"]["parameters"]["node_config"])
            dpath.util.merge(
                node_config,
                node_type["node_config"],
            )

            node_type["node_config"] = node_config

        auth: Dict = config.setdefault("auth", {})
        auth.setdefault("ssh_user", "root")

        if "ssh_private_key" not in auth:
            auth["ssh_private_key"] = str(
                TMP_PATH / get_default_ssh_key_name(config["cluster_name"])
            )

        # copy ssh details to provider namespace for cluster creation in __init__
        provider_parameters["_ssh_private_key"] = auth["ssh_private_key"]
        provider_parameters["_ssh_user"] = auth["ssh_user"]

    def _print_mainnet_onboarding_message(self, yagna_payment_status_output: str) -> None:
        if self._payment_network not in ONBOARDING_MESSAGE:
            return

        cli_logger.newline()

        with cli_logger.indented():
            cli_logger.print(ONBOARDING_MESSAGE.get(self._payment_network), no_format=True)
            cli_logger.print("Your wallet:")

            with cli_logger.indented():
                for line in yagna_payment_status_output.splitlines():
                    cli_logger.print(line, no_format=True)

            cli_logger.newline()
            cli_logger.print(
                "You can use the Golem Onboarding portal to top up: https://golemfactory.github.io"
                f"/onboarding_production/?yagnaAddress={self._wallet_address}"
                "\n\n"
                "DISCLAIMER: Please keep in mind that in its current stage, the Onboarding Portal "
                "is an EXPERIMENTAL product. Even though it is functional, "
                "we do not recommend using it unless you wish to help us beta-test this feature. "
                "You'll find more information on `#Payment UX` discord channel "
                "https://discord.com/channels/684703559954333727/1136984764197380096",
                no_format=True,
            )
            cli_logger.newline()
