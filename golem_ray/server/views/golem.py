import asyncio
import os
import subprocess
from asyncio.subprocess import Process
from ipaddress import IPv4Address
from pathlib import Path
from typing import List, Dict
from uuid import uuid4

import async_timeout
from golem_core.core.activity_api import commands
from golem_core.core.golem_node import GolemNode
from golem_core.core.market_api.pipeline import default_create_agreement, default_create_activity
from golem_core.managers.payment.default import DefaultPaymentManager
from golem_core.pipeline import Chain, Map, Buffer, Limit

from golem_ray.server.consts import StatusCode
from golem_ray.server.logger import get_logger
from golem_ray.server.middlewares.error_handling import GolemRayException
from golem_ray.server.models.cluster_node import ClusterNode
from golem_ray.server.utils.negotiation_utils import negotiate
from golem_ray.server.utils.utils import create_ssh_connection, parse_manifest, \
    get_or_create_yagna_appkey, create_reverse_ssh_to_golem_network
from models.types import NodeState, Node

logger = get_logger()


# "ssh -R '*:3001:127.0.0.1:6379' proxy@proxy.dev.golem.network"


class GolemNodeProvider:

    def __init__(self):
        self.ssh_tunnel_port = os.getenv('SSH_TUNNEL_PORT') or '3009'
        self.HEAD_IP = '192.168.0.2'
        self._proxy_ip = 'proxy.dev.golem.network'
        # self.HEAD_IP = '127.0.0.1'
        self._loop = None
        self._demand = None
        self._allocation = None
        self._network = None
        self._num_workers = None
        self._head_node_process: subprocess.Popen | None = None
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
        await self._allocation.get_data()

    def get_nodes_response(self) -> List[Node]:
        """
        Prepares ClusterNode instances data to pydantic Node class object
        """
        return [Node(node_id=cluster_node.node_id,
                     state=cluster_node.state,
                     internal_ip=cluster_node.internal_ip,
                     external_ip=cluster_node.external_ip,
                     tags=cluster_node.tags)
                for cluster_node in self._cluster_nodes]

    def get_node_response_by_id(self, node_id: int) -> Node:
        """
        Prepares single ClusterNode instance data to pydantic Node class Object
        """
        node = next((cluster_node for cluster_node in self._cluster_nodes if cluster_node.node_id == node_id), None)
        if not node:
            raise GolemRayException(message=f"No node with {node_id} id", status_code=StatusCode.BAD_REQUEST)
        return Node(node_id=node.node_id,
                    state=node.state,
                    internal_ip=node.internal_ip,
                    external_ip=node.external_ip,
                    tags=node.tags)

    async def create_cluster(self, provider_config: Dict):
        """
        Manages creating cluster, creates payload from given data and creates demand basing on payload
        Local node is being created without ray instance.
        :param provider_config: dictionary containing 'num_workers', and 'image_hash' keys
        """
        if self._demand:
            logger.info('Cluster was created already.')
            return
        self._num_workers = provider_config.get('num_workers', 4)
        payload, connection_timeout = await self._create_payload(provider_config=provider_config)
        self._demand = await self._golem.create_demand(payload,
                                                       allocations=[self._allocation],
                                                       autostart=True)
        self._reverse_ssh_process = await create_reverse_ssh_to_golem_network()

    async def start_head_process(self, tags=None):
        """
        Runs ray head node on local machine
        """
        if tags is None:
            tags = {}
        head_node = self._add_local_head_node(tags=tags)
        if head_node:
            if head_node.state == NodeState.pending:
                # TODO: Delete if sure that it won't be needed
                #     process = subprocess.Popen(
                #         ['ray', 'start', '--head', '--node-ip-address', '127.0.0.1', '--disable-usage-stats'])
                #     process.wait()
                #     if process:
                #         head_node.state = NodeState.running
                #         self._head_node_process = process
                head_node.state = NodeState.running
            elif head_node.state == NodeState.running:
                raise GolemRayException(message='Head node is already running ray', status_code=StatusCode.BAD_REQUEST)
        else:
            raise GolemRayException(message='Head node on local doesnt exist', status_code=StatusCode.BAD_REQUEST)

    async def start_workers(self, count: int, tags: Dict = None):
        """
        Creates {count} worker nodes on providers. No ray instances is running at the moment.
        :param tags: tags given by ray
        :param count: Quantity of workers that should be started
        """
        nodes_with_ray_on_count = sum([1 for x in self._cluster_nodes if x.state == NodeState.running])
        if count + nodes_with_ray_on_count > self._num_workers + 1:
            raise GolemRayException(message="Max workers limit exceeded", status_code=StatusCode.BAD_REQUEST)

        await self._create_activities(tags=tags)
        await self._network.refresh_nodes()
        await self._add_my_key()
        await self._add_other_keys()
        self._print_ws_connection_data()

        start_worker_tasks = []
        for node in self._cluster_nodes:
            if node.activity:
                node.state = NodeState.pending
                await self._start_worker_process(node.activity)
                node.state = NodeState.running

        if start_worker_tasks:
            await asyncio.gather(*start_worker_tasks)

    async def stop_worker(self, node_id: int):
        """
        Stops selected worker with {node_id} id.
        :param node_id: id of node where you want to stop ray
        """
        node = next((obj for obj in self._cluster_nodes if obj.node_id == node_id), None)
        if not node or not node.state.value != NodeState.running:
            raise GolemRayException(message=f"Node with id: {node_id} is not running ray!",
                                    status_code=StatusCode.BAD_REQUEST)
        if node_id != 0:
            await self._stop_node(node)
            self._cluster_nodes.remove(node)

    async def stop_workers_by_ids(self, workers_ids: List[int]):
        """
        Stops selected workers ray instances basing on id list
        :param workers_ids: list of workers id you want to stop ray on
        """
        nodes_to_stop = [node for node in self._cluster_nodes if node.node_id in workers_ids and node.node_id != 0]
        for node in nodes_to_stop:
            await self._stop_node(node)
            self._cluster_nodes.remove(node)

    async def set_node_tags(self, node_id: int, tags: Dict):
        """
        Updates selected cluster_node tags

        :param node_id: node_id to update
        :param tags: ray tags as dict
        :return:
        """
        node = next((obj for obj in self._cluster_nodes if obj.node_id == node_id), None)
        if node:
            node.tags.update(tags)

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

        await self._stop_local_head_node()
        logger.info(f'-----Ray on local machine stopped')

        if self._reverse_ssh_process:
            self._reverse_ssh_process.terminate()
            await asyncio.sleep(1)
            logger.info(f'-----Reverse ssh to {self._proxy_ip} closed.')
            self._reverse_ssh_process = None

    # Private

    def _get_head_node(self) -> ClusterNode | None:
        """
        Returns head node (ClusterNode obj) or None if not exists
        :return:
        """
        head_node = next((x for x in self._cluster_nodes if x.node_id == 0), None)
        if head_node:
            return head_node
        return None

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
        Adds keys from providers to local machine"
        :param key: ssh key
        :return:
        """
        result = subprocess.run(['echo', f"{key}", ">>", "~/.ssh/authorized_keys"])
        if result.returncode == 0:
            logger.info('-----ADDED PROVIDER KEY TO LOCAL')
        else:
            logger.info('-----FAILED ADDING PROVIDER KEY TO LOCAL')

    async def _create_payload(self, provider_config: dict, **kwargs):
        """
        Creates payload from given image_hash and parses manifest.json file
        which is then used to create demand in golem network
        :param provider_config: dictionary containing image_hash and num_workers
        :param kwargs:
        :return:
        """
        image_hash = provider_config.get('image_hash')
        payload, offer_scorer, connection_timeout = await parse_manifest(image_hash, self.ssh_tunnel_port)

        return payload, connection_timeout

    @staticmethod
    async def _stop_node(node: ClusterNode):
        """
        Stops ray process on selected node
        :param node: node to stop ray on
        :return:
        """
        if node and node.state == NodeState.running:
            batch = await node.activity.execute_commands(
                commands.Run(f'ray stop'),
            )
            try:
                await batch.wait(60)
                node.state = NodeState.pending
                await node.activity.destroy()
            except Exception:
                print(batch.events)
                print(f"Failed to stop a worker process with id: {node.node_id}")
                raise

    def _print_ws_connection_data(self) -> None:
        """
        Prints command which allows to manually ssh on providers machines
        :return:
        """
        for node in self._cluster_nodes:
            if node.node_id != 0:
                print(
                    "Connect with:\n"
                    f"ssh "
                    f"-o StrictHostKeyChecking=no "
                    f"-o ProxyCommand='websocat asyncstdio: {node.connection_uri}/22 --binary "
                    f"-H=Authorization:\"Bearer {self._golem._api_config.app_key}\"' root@{uuid4().hex} "
                )

    def _add_local_head_node(self, tags=None) -> ClusterNode:
        """
        Adds ClusterNode with node_id=0 (head_node) to list of nodes.

        :param tags: dict - contains ray tags
        :return:
        """
        if tags is None:
            tags = {}
        head_node = ClusterNode(node_id=0,
                                internal_ip=IPv4Address('127.0.0.1'),  # proxy.dev.golem.network
                                tags=tags)
        head_node.state = NodeState.pending
        self._cluster_nodes.append(head_node)

        return head_node

    async def _stop_local_head_node(self) -> None:
        self._get_head_node()
        head_node = self._get_head_node()
        if head_node and head_node.state == NodeState.running:
            process = await asyncio.create_subprocess_shell(
                'ray stop')
            await process.wait()
            if process and head_node:
                self._cluster_nodes.remove(head_node)
            self._head_node_process = None

    async def _start_worker_process(self, activity):
        """
        Starts ray worker process on external providers
        :param activity: Activity object from golem
        :return:
        """
        batch = await activity.execute_commands(
            commands.Run(f'ray start --address {self._proxy_ip}:{self.ssh_tunnel_port}'),
        )
        try:
            await batch.wait(60)
        except Exception:
            print(batch.events)
            print("Failed to start a worker process")
            raise

    async def _create_activities(self, connection_timeout=None, tags: Dict = None):
        """
        This functions manages demands, negotiations, agreements, creates activities
        and creates ssh connection to nodes.

        :param connection_timeout: Currently not used
        :return:
        """
        node_id = 1
        try:
            async with async_timeout.timeout(int(150)):
                chain = Chain(
                    self._demand.initial_proposals(),
                    # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                    Map(negotiate),
                    Map(default_create_agreement),
                    Map(default_create_activity),
                    Map(create_ssh_connection(self._network)),
                    Buffer(1),
                    Limit(self._num_workers))

                async for activity, ip, connection_uri in chain:
                    cluster_node = ClusterNode(node_id=node_id,
                                               activity=activity,
                                               internal_ip=IPv4Address(ip),
                                               connection_uri=connection_uri,
                                               tags=tags)
                    self._cluster_nodes.append(cluster_node)
                    logger.info(f'-----ACTIVITY YIELDED: {str(activity)}')
                    node_id += 1

        except asyncio.TimeoutError:
            raise GolemRayException(message="Creating activities timeout reached", status_code=StatusCode.SERVER_ERROR)

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
