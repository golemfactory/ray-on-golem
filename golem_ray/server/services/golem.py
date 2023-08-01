import asyncio
import base64
import os
from asyncio import subprocess
from asyncio.subprocess import Process
from datetime import timedelta
from ipaddress import IPv4Address
from pathlib import Path
from typing import List, Dict, Tuple
from uuid import uuid4

import async_timeout
from golem_core.core.activity_api import commands
from golem_core.core.golem_node import GolemNode
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.market_api.pipeline import default_create_agreement, default_create_activity
from golem_core.managers.payment.default import DefaultPaymentManager
from golem_core.pipeline import Chain, Map, Buffer, Limit

from golem_ray.server.logger import get_logger
from golem_ray.server.middlewares.error_handling import GolemRayException
from golem_ray.server.models.cluster_node import ClusterNode
from golem_ray.server.services.ssh import SSHService
from golem_ray.server.services.yagna import get_or_create_yagna_appkey
from golem_ray.server.utils.negotiation_utils import negotiate
from models.types import NodeState
from models.validation import CreateClusterRequest

logger = get_logger()


# "ssh -R '*:3001:127.0.0.1:6379' proxy@proxy.dev.golem.network"


class GolemService:

    def __init__(self):
        self.ssh_tunnel_port = os.getenv('SSH_TUNNEL_PORT') or '3009'
        self._proxy_ip = 'proxy.dev.golem.network'
        self._loop = None
        self._demand = None
        self._allocation = None
        self._network = None
        self._num_workers = None
        self._head_node_process: Process | None = None
        self._reverse_ssh_process: Process | None = None
        self._cluster_nodes: List[ClusterNode] = []
        self._golem = GolemNode(app_key=get_or_create_yagna_appkey())
        self._payment_manager: DefaultPaymentManager | None = None

    # Public api
    @property
    def golem(self):
        return self._golem

    @property
    def payment_manager(self) -> DefaultPaymentManager:
        return self._payment_manager

    async def init(self) -> None:
        async def on_event(event) -> None:
            logger.info(f'-----EVENT: {event}')

        self._golem.event_bus.listen(on_event)
        self._network = await self._golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)
        self._allocation = await self._golem.create_allocation(amount=1, network="goerli", autoclose=True)
        self._payment_manager = DefaultPaymentManager(self._golem, self._allocation)
        # await self._allocation.get_data()

    async def create_cluster(self, provider_config: CreateClusterRequest):
        """
        Manages creating cluster, creates payload from given data and creates demand basing on payload
        Local node is being created without ray instance.
        :param provider_config: dictionary containing 'num_workers', and 'image_hash' keys
        """
        if self._demand:
            logger.info('Cluster was created already.')
            return
        self._num_workers = provider_config.num_workers
        payload, connection_timeout = await self._create_payload(image_hash=provider_config.image_hash)
        self._demand = await self._golem.create_demand(payload,
                                                       allocations=[self._allocation],
                                                       autostart=True)
        self._reverse_ssh_process = await self._create_reverse_ssh_to_golem_network()

    async def get_providers(self, tags: Dict,
                            count: int,
                            current_nodes_count: int) -> List[Tuple[int, ClusterNode]]:
        new_nodes = await self._create_activities(tags=tags, count=count, current_nodes_count=current_nodes_count)
        await self._network.refresh_nodes()
        await self._add_my_key()
        await self._add_other_keys()
        self._print_ws_connection_data()

        return new_nodes

    async def shutdown(self) -> None:
        """
        Terminates all activities and ray on head node.
        Additionally, closes reverse ssh connection from local to proxy.

        :return:
        """
        await self.payment_manager.terminate_agreements()
        await self.payment_manager.wait_for_invoices()

        tasks = [node.activity.destroy() for node in self._cluster_nodes if node.activity]
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f'-----{len(tasks)} activities stopped')

        if self._reverse_ssh_process:
            self._reverse_ssh_process.terminate()
            await self._reverse_ssh_process.wait()
            logger.info(f'-----Reverse ssh to {self._proxy_ip} closed.')
            self._reverse_ssh_process = None

    # Private
    @staticmethod
    async def _create_reverse_ssh_to_golem_network() -> Process:
        """
        Creates reverse tunnel to golem network

        :return: shell subprocess which runs reverse tunnel
        """
        process = await subprocess.create_subprocess_shell(
            rf"ssh -N -R *:{os.getenv('SSH_TUNNEL_PORT')}:127.0.0.1:6379 proxy@proxy.dev.golem.network")
        logger.info(f'Reverse ssh tunnel from 127.0.0.1:6379 to *:{os.getenv("SSH_TUNNEL_PORT")} created.')

        return process

    @staticmethod
    async def _add_authorized_key(activity, key):
        """
        Adds local machine ssh key to providers machine
        :param activity: Activity object from golem
        :param key: Key you want to add to authorized_keys on provider machine
        """
        batch = await activity.execute_commands(
            commands.Run('mkdir -p /root/.ssh'),
            commands.Run(f'echo "{key}" >> /root/.ssh/authorized_keys'),
        )
        try:
            await batch.wait(15)
        except Exception:
            print(batch.events)
            raise

    @staticmethod
    async def _add_authorized_key_to_local_node(key):
        """
        Adds keys from providers to local machine
        :param key: ssh key
        :return:
        """
        result = await subprocess.create_subprocess_exec('echo', f"{key}", ">>", "~/.ssh/authorized_keys")
        await result.communicate()
        if result.returncode == 0:
            logger.info('-----ADDED PROVIDER KEY TO LOCAL')
        else:
            logger.info('-----FAILED ADDING PROVIDER KEY TO LOCAL')

    async def _create_payload(self, image_hash: str, **kwargs):
        """
        Creates payload from given image_hash and parses manifest.json file
        which is then used to create demand in golem network
        :param provider_config: dictionary containing image_hash and num_workers
        :param kwargs:
        :return:
        """
        payload, offer_scorer, connection_timeout = await self._parse_manifest(image_hash, self.ssh_tunnel_port)

        return payload, connection_timeout

    def _print_ws_connection_data(self) -> None:
        """
        Prints command which allows to manually ssh on providers machines
        :return:
        """
        for node in self._cluster_nodes:
            if node.activity:
                print(
                    "Connect with:\n"
                    f"ssh "
                    f"-o StrictHostKeyChecking=no "
                    f"-o ProxyCommand='websocat asyncstdio: {node.connection_uri}/22 --binary "
                    f"-H=Authorization:\"Bearer {self._golem._api_config.app_key}\"' root@{uuid4().hex} "
                )

    async def _create_activities(self,
                                 count: int,
                                 current_nodes_count: int,
                                 tags: Dict = None) -> List[Tuple[int, ClusterNode]]:
        """
        This functions manages demands, negotiations, agreements, creates activities
        and creates ssh connection to nodes.

        :param connection_timeout: Currently not used
        :return:
        """
        try:
            new_nodes = []
            node_id = current_nodes_count
            async with async_timeout.timeout(int(150)):
                chain = Chain(
                    self._demand.initial_proposals(),
                    # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                    Map(negotiate),
                    Map(default_create_agreement),
                    Map(default_create_activity),
                    Map(SSHService.create_ssh_connection(self._network)),
                    Buffer(1),
                    Limit(count))

                async for activity, ip, connection_uri in chain:
                    cluster_node = ClusterNode(node_id=node_id,
                                               activity=activity,
                                               internal_ip=IPv4Address(ip),
                                               connection_uri=connection_uri,
                                               tags=tags,
                                               state=NodeState.pending)
                    new_nodes.append((node_id, cluster_node))
                    node_id += 1
                    logger.info(f'-----ACTIVITY YIELDED: {str(activity)}')

                return new_nodes

        except asyncio.TimeoutError:
            raise GolemRayException(message="Creating activities timeout reached")

    async def _add_my_key(self):
        """
        Add local ssh key to all providers
        """
        with open(Path.home() / '.ssh/id_rsa.pub', 'r') as f:
            my_key = f.readline().strip()

        tasks = [self._add_authorized_key(value.activity, my_key) for value in self._cluster_nodes if value.activity]
        await asyncio.gather(*tasks)

    async def _add_other_keys(self):
        """
        Adds all providers key to other providers machines
        """
        keys = {}
        for cluster_node in self._cluster_nodes:
            if cluster_node.activity:
                batch = await cluster_node.activity.execute_commands(
                    commands.Run('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'),
                    commands.Run('cat /root/.ssh/id_rsa.pub'),
                )
                await batch.wait()
                key = batch.events[-1].stdout.strip()
                keys[cluster_node.node_id] = key

        for cluster_node in self._cluster_nodes:
            other_nodes: List[ClusterNode] = [node for node in self._cluster_nodes if
                                              node.node_id != cluster_node.node_id]

            for other_node in other_nodes:
                if other_node.node_id == 0:
                    continue
                other_activity_key = keys[other_node.node_id]
                if cluster_node.activity:
                    await self._add_authorized_key(cluster_node.activity, other_activity_key)
                else:
                    await self._add_authorized_key_to_local_node(other_activity_key)

    @staticmethod
    async def _parse_manifest(image_hash: str, ssh_tunnel_port: str, text=None):
        """Parses manifest file and replaces image_hash used.
           Decoding is needed in order to work.
           :arg image_hash:
           :arg text:
        """
        # TODO: refactor parent.parent...parent - define ROOT_DIR
        with open(Path(__file__).parent.parent.parent.parent.joinpath("manifest.json"), "rb") as manifest:
            manifest = manifest.read()
            manifest = (manifest
                        .decode('utf-8')
                        .replace('{IMAGE_HASH}', image_hash)
                        .replace('{SSH_TUNNEL_PORT}', ssh_tunnel_port)
                        )
            manifest = base64.b64encode(manifest.encode('utf-8')).decode("utf-8")

            params = {
                "manifest": manifest,
                "capabilities": ['vpn', 'inet', 'manifest-support'],
                "min_mem_gib": 0,
                "min_cpu_threads": 0,
                "min_storage_gib": 0,
            }
            # strategy = DEFAULT_SCORING_STRATEGY
            # connection_timeout = DEFAULT_CONNECTION_TIMEOUT
            connection_timeout = timedelta(seconds=150)
            offer_scorer = None
            payload = ManifestVmPayload(**params)

            return payload, offer_scorer, connection_timeout
