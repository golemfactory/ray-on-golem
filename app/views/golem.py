import asyncio
import base64
import json
import os
import logging
import subprocess
from uuid import uuid4

import async_timeout
from pytimeparse import parse as parse_to_seconds
from datetime import timedelta
from random import random
from subprocess import check_output, check_call
from ipaddress import IPv4Address

from aiohttp import web
from pathlib import Path
from typing import Awaitable, Callable, Tuple, Any, List, Generator, Dict
from urllib.parse import urlparse

from models.response import GetNodesResponse
from models.types import NodeState, Node

from golem_core.core.activity_api import commands
from golem_core.core.golem_node import GolemNode
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.activity_api.resources import Activity
from golem_core.core.network_api.resources import Network
from golem_core.core.market_api.pipeline import default_negotiate, default_create_agreement, default_create_activity
from golem_core.pipeline import Chain, Map, Buffer, Limit

from app.models.cluster_node import ClusterNode

YAGNA_APPNAME = 'requestor-mainnet'

# TODO: move to method
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# "ssh -R '*:3001:127.0.0.1:6379' proxy@proxy.dev.golem.network"
async def negotiate(proposal):
    return await asyncio.wait_for(default_negotiate(proposal), timeout=10)


async def bestprice_score(proposal):
    properties = proposal.data.properties
    if properties['golem.com.pricing.model'] != 'linear':
        return None

    coeffs = properties['golem.com.pricing.model.linear.coeffs']
    return 1 - (coeffs[0] + coeffs[1])


async def random_score(proposal):
    return random()


STRATEGY_SCORING_FUNCTION = {"bestprice": bestprice_score, "random": random_score}
DEFAULT_SCORING_STRATEGY = "bestprice"
DEFAULT_CONNECTION_TIMEOUT = timedelta(minutes=5)


# -R *:3001:127.0.0.1:6379 proxy@proxy.dev.golem.network
def create_ssh_connection(network: Network) -> Callable[[Activity], Awaitable[Tuple[str, str]]]:
    async def _create_ssh_connection(activity: Activity) -> Tuple[Activity, Any, str]:
        #   1.  Create node
        provider_id = activity.parent.parent.data.issuer_id
        assert provider_id is not None  # mypy
        ip = await network.create_node(provider_id)

        #   2.  Run commands
        deploy_args = {"net": [network.deploy_args(ip)]}

        batch = await activity.execute_commands(
            commands.Deploy(deploy_args),
            commands.Start(),
            commands.Run('service ssh start'),
            # commands.Run('ssh -R "*:3001:127.0.0.1:6379" proxy@proxy.dev.golem.network'),
        )
        await batch.wait(600)

        #   3.  Create connection uri
        url = network.node._api_config.net_url
        net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
        connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}"

        return activity, ip, connection_uri

    return _create_ssh_connection


class GolemNodeProvider:

    def __init__(self):
        self.HEAD_IP = '192.168.0.2'
        # self.HEAD_IP = '127.0.0.1'
        self._loop = None
        self._demand = None
        self._allocation = None
        self._network = None
        self._connections = {}
        self._worker_nodes = {}
        self._num_workers = None
        self._nodes = {}
        self._cluster_nodes: List[ClusterNode] = []
        self._golem = GolemNode(app_key=self._get_or_create_yagna_appkey())

    def get_nodes_response(self) -> List[Node]:
        return [Node(node_id=cluster_node.node_id,
                     state=cluster_node.state,
                     internal_ip=cluster_node.internal_ip,
                     external_ip=cluster_node.external_ip) for cluster_node in self._cluster_nodes]

    def get_node_response_by_id(self, node_id: str):
        node = next((cluster_node for cluster_node in self._cluster_nodes if cluster_node.node_id == node_id), None)
        if not node:
            raise web.HTTPBadRequest(body=f"No node with {node_id} id")
        return Node(node_id=node.node_id,
                    state=node.state,
                    internal_ip=node.internal_ip,
                    external_ip=node.external_ip)

    @property
    def golem(self) -> GolemNode:
        """Golem getter"""
        return self._golem

    @property
    def nodes(self) -> dict:
        """Nodes getter"""
        return self._nodes

    async def init(self) -> None:
        async def on_event(event) -> None:
            logger.info(f'-----EVENT: {event}')
        self._golem.event_bus.listen(on_event)
        self._network = await self._golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
        self._allocation = await self._golem.create_allocation(amount=1, network="goerli")

        await self._allocation.get_data()

    def _get_or_create_yagna_appkey(self):
        if os.getenv('YAGNA_APPKEY') is None:
            id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))
            yagna_app = next((app for app in id_data if app['name'] == YAGNA_APPNAME), None)
            if yagna_app is None:
                return check_output(["yagna", "app-key", "create", YAGNA_APPNAME]).decode('utf-8').strip('"\n')
            else:
                return yagna_app['key']
        else:
            return os.getenv('YAGNA_APPKEY')

    @staticmethod
    def get_value_from_dict_or_throw(d, k):
        if k in d:
            return d[k]
        else:
            raise web.HTTPBadRequest(body=f"'{k}' is needed")

    def print_ws_connection_data(self) -> None:
        for node in self._cluster_nodes:
            print(
                "Connect with:\n"
                f"ssh "
                f"-o StrictHostKeyChecking=no "
                f"-o ProxyCommand='websocat asyncstdio: {node.connection_uri}/22 --binary "
                f"-H=Authorization:\"Bearer {self._golem._api_config.app_key}\"' root@{uuid4().hex} "
            )

    async def create_demand(self, provider_config: Dict):
        payload, connection_timeout = await self.create_payload(provider_config=provider_config)
        self._demand = await self._golem.create_demand(payload, allocations=[self._allocation], autostart=True)

        await self.create_activities(provider_config, connection_timeout)
        await self._network.refresh_nodes()
        await self._add_my_key()
        await self._add_other_keys()
        await self._start_head_process()
        self.print_ws_connection_data()

    @staticmethod
    async def _parse_manifest(image_hash, text=None):
        """Parses manifest file and replaces image_hash used.
           Decoding is needed in order to work.
           :arg image_hash:
           :arg text:
        """
        manifest = open(Path(__file__).parent.parent.parent.joinpath("manifest.json"), "rb").read()
        manifest = (manifest
                    .decode('utf-8')
                    .replace('{sha3}', image_hash)
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

    async def create_payload(self, provider_config: dict, **kwargs):
        image_hash = self.get_value_from_dict_or_throw(provider_config, 'image_hash')
        payload, offer_scorer, connection_timeout = await self._parse_manifest(image_hash)

        return payload, connection_timeout

    async def create_activities(self, provider_config, connection_timeout):
        self._num_workers = provider_config.get('num_workers', 4)
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
                    cluster_node = ClusterNode(node_id=str(node_id),
                                               activity=activity,
                                               internal_ip=IPv4Address(ip),
                                               connection_uri=connection_uri)
                    self._cluster_nodes.append(cluster_node)
                    logger.info(f'-----ACTIVITY YIELDED: {str(activity)}')
                    node_id += 1

        # TODO: raise not by web (write own exception)
        except asyncio.TimeoutError:
            raise web.HTTPBadRequest(body="Creating activities timeout reached")

    @staticmethod
    async def add_authorized_key(activity, key):
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
    async def add_authorized_key_to_local_node(key):
        result = subprocess.run(['echo', f"{key}", ">>", "/root/.ssh/authorized_keys"])
        if result.returncode == 0:
            logger.info('-----ADDED PROVIDER KEY TO LOCAL')
        else:
            logger.info('-----FAILED ADDING PROVIDER KEY TO LOCAL')

    async def _add_my_key(self):
        with open(Path.home() / '.ssh/id_rsa.pub', 'r') as f:
            my_key = f.readline().strip()

        tasks = [self.add_authorized_key(value.activity, my_key) for value in self._cluster_nodes if value.activity]
        await asyncio.gather(*tasks)

    async def _add_other_keys(self):
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
                other_activity_key = keys[other_node.node_id]
                if cluster_node.activity:
                    await self.add_authorized_key(cluster_node.activity, other_activity_key)
                else:
                    await self.add_authorized_key_to_local_node(other_activity_key)

    # async def _start_head_process(self):
    #     head_node = next((node for node in self._cluster_nodes if str(node.internal_ip) == self.HEAD_IP), None)
    #     if head_node:
    #         head_node.state = NodeState.running
    #         batch = await head_node.activity.execute_commands(
    #             commands.Run(
    #                 f'ray start --head --include-dashboard=True --node-ip-address {self.HEAD_IP} --disable-usage-stats'),
    #         )
    #         await batch.wait(20)

    async def _start_head_process(self):
        head_node = ClusterNode(node_id='0', internal_ip=IPv4Address(self.HEAD_IP))
        process = subprocess.Popen(
            ['ray', 'start', '--head', ' --autoscaling-config', '~/ray_bootstrap_config.yaml' '--node-ip-address', '127.0.0.1', '--disable-usage-stats'])
        process.wait()
        if process:
            head_node.state = NodeState.running
            self._cluster_nodes.append(head_node)

    async def _start_worker_process(self, activity):
        batch = await activity.execute_commands(
            commands.Run(f'ray start --address {self.HEAD_IP}:6379'),
        )
        try:
            await batch.wait(60)
        except Exception:
            print(batch.events)
            print("Failed to start a worker process")
            raise

    async def start_workers(self, count: int):
        nodes_with_ray_on_count = sum([1 for x in self._cluster_nodes if x.state == NodeState.running])
        if count + nodes_with_ray_on_count > self._num_workers + 1:
            raise web.HTTPBadRequest(body="Max workers limit exceeded")

        start_worker_tasks = []
        for node in self._cluster_nodes:
            if node.internal_ip != self.HEAD_IP:
                node.state = NodeState.running

        if start_worker_tasks:
            await asyncio.gather(*start_worker_tasks)

        return self._nodes

    async def stop_worker(self, node_id: int):
        node = next((obj for obj in self._cluster_nodes if obj.node_id == str(node_id)), None)
        if not node or not node.state.value != NodeState.running:
            raise web.HTTPBadRequest(body=f"Node with id: {node_id} is not running ray!")
        if node and node_id != 0:
            activity = node.activity
            batch = await activity.execute_commands(
                commands.Run(
                    f'ray stop'),
            )
            try:
                await batch.wait(60)
                node.state = NodeState.pending
            except Exception:
                print(batch.events)
                print("Failed to stop a worker process")
                raise
