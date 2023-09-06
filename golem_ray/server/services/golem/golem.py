import asyncio
import base64
import hashlib
import json
import logging
import platform
from asyncio.subprocess import Process
from getpass import getuser
from ipaddress import IPv4Address
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import aiohttp
import async_timeout
import ray
from golem_core.core.activity_api import commands
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
from golem_ray.server.services.ssh import SshService

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
        self._num_workers: Optional[int] = None
        self._head_node_process: Optional[Process] = None
        self._reverse_ssh_process: Optional[Process] = None
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
            logger.debug(f"-----EVENT: {event}")

        self._golem.event_bus.listen(on_event)
        self._network = await self._golem.create_network(
            "192.168.0.1/24"
        )  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)
        self._allocation = await self._golem.create_allocation(
            amount=1, network="goerli", autoclose=True
        )
        self._payment_manager = DefaultPaymentManager(self._golem, self._allocation)

        key_hash = hashlib.md5(getuser().encode()).hexdigest()[:10]
        self._temp_ssh_key_dir = Path("/tmp/golem-ray-ssh")
        self._temp_ssh_key_filename = f"golem_ray_rsa_{key_hash}"

        await SshService.create_temporary_ssh_key(
            ssh_key_dir=self._temp_ssh_key_dir, ssh_key_filename=self._temp_ssh_key_filename
        )
        # await self._allocation.get_data()

    async def shutdown(self) -> None:
        """
        Terminates all activities and ray on head node.
        Additionally, closes reverse ssh connection from local to proxy.

        :return:
        """
        await self.payment_manager.terminate_agreements()
        await self.payment_manager.wait_for_invoices()

        tasks = [node.activity.destroy() for node in self._cluster_nodes.values() if node.activity]
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"-----{len(tasks)} activities stopped")

        if self._reverse_ssh_process and self._reverse_ssh_process.returncode is None:
            self._reverse_ssh_process.terminate()
            await self._reverse_ssh_process.wait()
            logger.info(f"-----Reverse ssh to *:{self._golem_ray_port} closed.")
            self._reverse_ssh_process = None

        await SshService.remove_temporary_ssh_key(
            self._temp_ssh_key_dir, self._temp_ssh_key_filename
        )

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

        self._num_workers = provider_config.num_workers

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
        await self._add_other_keys()  # TODO: Fix adding other keys
        self._print_ws_connection_data()

        if not self._reverse_ssh_process:
            self._reverse_ssh_process = await self._create_reverse_ssh_to_golem_network()

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

    async def get_head_node_ip(self) -> IPv4Address:
        head_node = await self._get_head_node()
        return head_node.internal_ip

    async def _create_reverse_ssh_to_golem_network(self) -> Process:
        """
        Creates reverse tunnel to golem network

        :return: shell subprocess which runs reverse tunnel
        """
        head_node = await self._get_head_node()
        proxy_command = self.get_node_ssh_proxy_command(head_node.node_id)
        # text_command = f"ssh -N -R -o StrictHostKeyChecking=no *:{self._golem_ray_port}:127.0.0.1:{self._golem_ray_port} proxy@proxy.dev.golem.network"
        text_command = (
            f"ssh -N -R '*:{self._golem_ray_port}:127.0.0.1:{self._golem_ray_port}' "
            f"-o StrictHostKeyChecking=no "
            f'-o ProxyCommand="{proxy_command}" '
            f"-i {self._temp_ssh_key_dir / self._temp_ssh_key_filename} "
            f"root@{uuid4().hex}"
        )

        process = await asyncio.create_subprocess_shell(
            text_command,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        logger.info(
            f"Reverse ssh tunnel from 127.0.0.1:{self._golem_ray_port} to *:{self._golem_ray_port} created."
        )

        return process

    @staticmethod
    async def _add_authorized_key(activity, key):
        # TODO: Creating temporary key for ray cluster instance
        """
        Adds local machine ssh key to providers machine
        :param activity: Activity object from golem
        :param key: Key you want to add to authorized_keys on provider machine
        """
        batch = await activity.execute_commands(
            commands.Run("mkdir -p /root/.ssh"),
            commands.Run("touch /root/.ssh/authorized_keys"),
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

        params = node_config.dict(exclude={"image_url", "image_hash", "image_tag"})
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

        return await self._get_image_url_and_hash_from_tag(image_tag)

    @staticmethod
    async def _get_image_url_from_hash(image_hash: str) -> URL:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"hash": image_hash},
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return URL(response_data["http"])
                elif response.status == 404:
                    raise RegistryRequestError(f"Image hash {image_hash} does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")

    @staticmethod
    async def _get_image_url_and_hash_from_tag(image_tag: Optional[str]) -> Tuple[URL, str]:
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

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"tag": f"loop/golem-ray:{image_tag}"},
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
                    f"ssh "
                    f"-o StrictHostKeyChecking=no "
                    f"-o ProxyCommand='{self._websocat_path} asyncstdio: {node.connection_uri}/22 --binary "
                    f'-H=Authorization:"Bearer {self._golem._api_config.app_key}"\' root@{uuid4().hex} '
                    # f"-i ${str(self._temp_ssh_key_dir)}/${self._temp_ssh_key_filename}"
                )

    def get_node_ssh_proxy_command(self, node_id: NodeId) -> str:
        node = self._cluster_nodes.get(node_id)

        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {node.connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"

    async def _create_activities(self, count: int, tags: Dict = None) -> None:
        """
        This functions manages demands, negotiations, agreements, creates activities
        and creates ssh connection to nodes.

        :param connection_timeout: Currently not used
        :return:
        """
        async with self._lock:
            try:  # TODO: upload golem_ray files
                async with async_timeout.timeout(int(150)):
                    chain = Chain(
                        self._demand.initial_proposals(),
                        # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                        Map(self._negotiate),
                        Map(default_create_agreement),
                        Map(default_create_activity),
                        Map(SshService.create_ssh_connection(self._network)),
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
                            logger.debug(f"-----ACTIVITY YIELDED: {str(activity)}")

            except asyncio.TimeoutError:
                raise CreateActivitiesTimeout

    async def _add_my_key(self):
        """
        Add local ssh key to all providers
        """
        async with self._lock:
            id_rsa_file_path = self._temp_ssh_key_dir / (self._temp_ssh_key_filename + ".pub")

            if not id_rsa_file_path.exists():
                logger.error("{} not exists. SSH connection may fail.".format(id_rsa_file_path))
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

    async def _add_other_keys(self):
        """
        Adds all providers key to other providers machines
        """
        async with self._lock:
            keys = {}
            cluster_nodes = list(self._cluster_nodes.values())
            for cluster_node in cluster_nodes:
                if cluster_node.activity:
                    batch = await cluster_node.activity.execute_commands(
                        commands.Run(
                            '[ -f /root/.ssh/id_rsa ] || ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'
                        ),
                        commands.Run("cat /root/.ssh/id_rsa.pub"),
                    )
                    await batch.wait()
                    key = batch.events[-1].stdout.strip()
                    logger.info(f"{cluster_node.node_id} - key: {key}")
                    keys[cluster_node.node_id] = key

            for cluster_node in cluster_nodes:
                other_nodes: List[ClusterNode] = [
                    node for node in cluster_nodes if node.node_id != cluster_node.node_id
                ]

                for other_node in other_nodes:
                    other_activity_key = keys[other_node.node_id]
                    if cluster_node.activity:
                        await self._add_authorized_key(cluster_node.activity, other_activity_key)

    @staticmethod
    async def _negotiate(proposal):
        return await asyncio.wait_for(default_negotiate(proposal), timeout=10)
