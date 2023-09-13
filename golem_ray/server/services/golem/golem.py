import asyncio
import base64
import json
import logging
import platform
from asyncio.subprocess import Process
from ipaddress import IPv4Address
from pathlib import Path
from typing import Dict, Optional, Tuple

import aiohttp
import async_timeout
import ray
from golem_core.core.activity_api import Activity, BatchError, commands
from golem_core.core.golem_node import GolemNode
from golem_core.core.market_api import Demand, ManifestVmPayload
from golem_core.core.market_api.pipeline import (
    default_create_activity,
    default_create_agreement,
    default_negotiate,
)
from golem_core.core.network_api import Network
from golem_core.core.payment_api import Allocation
from golem_core.managers.payment.default import DefaultPaymentManager
from golem_core.pipeline import Buffer, Chain, Limit, Map
from yarl import URL

from golem_ray.server.exceptions import (
    CreateActivitiesTimeout,
    DestroyActivityError,
    GolemRayServerError,
    RegistryRequestError,
)
from golem_ray.server.models import (
    ClusterNode,
    CreateClusterRequestData,
    NodeConfigData,
    NodeId,
    NodeState,
)
from golem_ray.server.services.golem.manifest import get_manifest
from golem_ray.server.settings import TMP_PATH
from golem_ray.utils import get_ssh_key_name

logger = logging.getLogger(__name__)


# "ssh -R '*:3001:127.0.0.1:6379' proxy@proxy.dev.golem.network"


class GolemService:
    def __init__(self, golem_ray_port: int, websocat_path: Path):
        self._golem_ray_port = golem_ray_port
        self._websocat_path = websocat_path

        self._golem: Optional[GolemNode] = None
        self._demand: Optional[Demand] = None
        self._allocation: Optional[Allocation] = None
        self._network: Optional[Network] = None
        self._cluster_nodes: Dict[NodeId, ClusterNode] = {}
        self._payment_manager: Optional[DefaultPaymentManager] = None
        self._yagna_appkey: Optional[str] = None
        self._temp_ssh_key_dir: Optional[Path] = None
        self._temp_ssh_key_filename: Optional[str] = None
        self._lock = asyncio.Lock()

    @property
    def golem(self):
        return self._golem

    @property
    def cluster_nodes(self):
        return self._cluster_nodes

    @property
    def payment_manager(self) -> DefaultPaymentManager:
        return self._payment_manager

    async def init(self, yagna_appkey: str) -> None:
        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        async def on_event(event) -> None:
            logger.debug(f"----- EVENT: {event}")

        self._golem.event_bus.listen(on_event)
        self._network = await self._golem.create_network(
            "192.168.0.1/24"
        )  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)
        self._allocation = await self._golem.create_allocation(
            amount=1, network="goerli", autoclose=True
        )
        self._payment_manager = DefaultPaymentManager(self._golem, self._allocation)

    async def shutdown(self) -> None:
        """
        Terminates all activities and ray on head node.
        Additionally, closes reverse ssh connection from local to proxy.

        :return:
        """
        await self.payment_manager.terminate_agreements()
        tasks = [node.activity.destroy() for node in self._cluster_nodes.values() if node.activity]
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"----- {len(tasks)} activities stopped")

        logger.info(f"----- Waiting for all invoices...")
        await self.payment_manager.wait_for_invoices()
        logger.info(f"----- All invoices paid")

        await self._golem.aclose()
        self._golem = None

    async def create_cluster(self, provider_config: CreateClusterRequestData):
        """
        Manages creating cluster, creates payload from given data and creates demand basing on payload
        Local node is being created without ray instance.
        :param provider_config: dictionary containing 'num_workers', and 'image_hash' keys
        """
        if self._demand:
            logger.info("Cluster was created already.")
            return

        self._cluster_name = provider_config.cluster_name
        self._temp_ssh_key_dir = TMP_PATH
        self._temp_ssh_key_filename = get_ssh_key_name(self._cluster_name)

        payload = await self._create_payload(provider_config.node_config)
        self._demand = await self._golem.create_demand(
            payload, allocations=[self._allocation], autostart=True
        )

    async def get_providers(
        self,
        tags: Dict,
        count: int,
    ) -> None:
        """
        Creates activities (demand providers) in golem network
        :param tags: tags from ray
        :param count: number of nodes to create
        :param current_nodes_count: current count of running nodes
        :return:
        """
        await self._create_activities(tags=tags, count=count)
        await self._network.refresh_nodes()
        await self._add_my_key()
        self._print_ws_connection_data()

    @staticmethod
    async def destroy_activity(node: ClusterNode):
        try:
            await node.activity.destroy()
        except Exception:
            raise DestroyActivityError

    async def _get_head_node(self) -> ClusterNode:
        async with self._lock:
            for node in self._cluster_nodes.values():
                ray_node_type = node.tags.get("ray-node-type")
                if ray_node_type == "head":
                    return node

    @staticmethod
    async def _add_authorized_key(activity, key):
        """
        Adds local machine ssh key to providers machine
        :param activity: Activity object from golem
        :param key: Key you want to add to authorized_keys on provider machine
        """
        batch = await activity.execute_commands(
            commands.Run("mkdir -p /root/.ssh"),
            commands.Run(f'echo "{key}" >> /root/.ssh/authorized_keys'),
        )
        try:
            await batch.wait(15)
            logger.info("Added local ssh key to provider with id: {}".format(activity.id))
        except Exception:
            print(batch.events)
            raise

    async def _create_payload(self, node_config: NodeConfigData) -> ManifestVmPayload:
        """
        Creates payload from given image_hash and parses manifest.json file
        which is then used to create demand in golem network
        :param node_config: dictionary containing image_hash and num_workers
        :return:
        """
        image_url, image_hash = await self._get_image_url_and_hash(node_config)

        manifest = get_manifest(image_url, image_hash)
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = node_config.dict(exclude={"image_hash", "image_tag"})
        params["manifest"] = manifest

        payload = ManifestVmPayload(**params)

        return payload

    async def _get_image_url_and_hash(self, node_config: NodeConfigData) -> Tuple[URL, str]:
        image_tag = node_config.image_tag
        image_hash = node_config.image_hash

        if image_tag is not None and image_hash is not None:
            raise GolemRayServerError(
                "Only one of 'image_tag' and 'image_hash' parameter should be defined!"
            )

        if image_hash is not None:
            image_url = await self._get_image_url_from_hash(image_hash)
            return image_url, image_hash

        if image_tag is None:
            python_version = platform.python_version()
            ray_version = ray.__version__
            image_tag = f"golem/ray-on-golem:py{python_version}-ray{ray_version}"

        return await self._get_image_url_and_hash_from_tag(image_tag)

    @staticmethod
    async def _get_image_url_from_hash(image_hash: str) -> URL:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"hash": image_hash, "count": "true"},
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return URL(response_data["http"])
                elif response.status == 404:
                    raise RegistryRequestError(f"Image hash {image_hash} does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")

    @staticmethod
    async def _get_image_url_and_hash_from_tag(image_tag: str) -> Tuple[URL, str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"tag": image_tag, "count": "true"},
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data["http"], response_data["sha3"]
                elif response.status == 404:
                    raise RegistryRequestError(f"Image tag '{image_tag}' does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")

    def _print_ws_connection_data(self) -> None:
        """
        Prints command which allows to manually ssh on providers machines
        :return:
        """
        for node in self._cluster_nodes.values():
            if node.activity:
                print(
                    "Connect with:\n"
                    "ssh "
                    "-o StrictHostKeyChecking=no "
                    "-o UserKnownHostsFile=/dev/null "
                    f"-o ProxyCommand='{self._websocat_path} asyncstdio: {node.connection_uri}/22 --binary "
                    f'-H=Authorization:"Bearer {self._golem._api_config.app_key}"\' root@{node.internal_ip} '
                    # f"-i ${str(self._temp_ssh_key_dir)}/${self._temp_ssh_key_filename}"
                )

    def get_node_ssh_proxy_command(self, node_id: NodeId) -> str:
        node = self._cluster_nodes.get(node_id)

        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {node.connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"

    async def _add_my_key(self):
        """
        Add local ssh key to all providers
        """
        async with self._lock:
            id_rsa_file_path = self._temp_ssh_key_dir / (self._temp_ssh_key_filename + ".pub")

            if not id_rsa_file_path.exists():
                logger.error(f"{id_rsa_file_path} not exists. SSH connection may fail.")
                return

            # TODO: Use async file handling
            with id_rsa_file_path.open() as f:
                my_key = f.readline().strip()

            tasks = [
                self._add_authorized_key(value.activity, my_key)
                for value in self._cluster_nodes.values()
                if value.activity
            ]

            await asyncio.gather(*tasks)

    async def _create_activities(self, count: int, tags: Dict = None) -> None:
        """
        This functions manages demands, negotiations, agreements, creates activities
        and creates ssh connection to nodes.

        :param connection_timeout: Currently not used
        :return:
        """
        async with self._lock:
            try:
                async with async_timeout.timeout(int(150)):
                    chain = Chain(
                        self._demand.initial_proposals(),
                        # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                        Map(self._negotiate),
                        Map(default_create_agreement),
                        Map(default_create_activity),
                        Map(self._deploy_with_vpn_and_start),
                        Map(self._bootstrap_host),
                        Buffer(1),
                        Limit(count),
                    )

                    async for activity, ip, connection_uri in chain:
                        node_id = len(self._cluster_nodes)
                        cluster_node = ClusterNode(
                            node_id=node_id,
                            activity=activity,
                            internal_ip=IPv4Address(ip),
                            connection_uri=connection_uri,
                            tags=tags,
                            state=NodeState.pending,
                        )
                        found = next(
                            (x for x in self.cluster_nodes.values() if x.internal_ip == ip), None
                        )
                        if not found:
                            self._cluster_nodes[node_id] = cluster_node

            except asyncio.TimeoutError:
                raise CreateActivitiesTimeout

    @staticmethod
    async def _negotiate(proposal):
        return await asyncio.wait_for(default_negotiate(proposal), timeout=10)

    async def _deploy_with_vpn_and_start(self, activity: Activity) -> Tuple[Activity, str]:
        provider_id = activity.parent.parent.data.issuer_id
        assert provider_id is not None  # mypy
        ip = await self._network.create_node(provider_id)

        deploy_args = {"net": [self._network.deploy_args(ip)]}

        batch = await activity.execute_commands(
            commands.Deploy(deploy_args),
            commands.Start(),
        )

        try:
            await batch.wait(600)
        except BatchError:
            # FIXME: image_url should be freely available instead
            provider_name = activity.parent.parent.data.properties["golem.node.id.name"]
            manifest = json.loads(
                base64.b64decode(
                    activity.parent.parent.demand.data.properties["golem.srv.comp.payload"]
                )
            )
            image_url = manifest["payload"][0]["urls"][0]
            print(
                f"Provider '{provider_name}' deploy failed on image '{image_url}' with batch id: '{batch.id}'"
            )
            raise

        return activity, ip

    async def _bootstrap_host(self, activity: Activity, ip: str) -> Tuple[Activity, str, str]:
        hostname = ip.replace(".", "-")

        batch = await activity.execute_commands(
            commands.Run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment"),
            commands.Run(f"hostname '{hostname}'"),
            commands.Run(f"echo '{hostname}' > /etc/hostname"),
            commands.Run(f"echo '{ip} {hostname}' >> /etc/hosts"),
            commands.Run("service ssh start"),
        )
        await batch.wait(15)

        network_url = URL(self._network.node._api_config.net_url)
        connection_uri = network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

        return activity, ip, str(connection_uri)
