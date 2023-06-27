import asyncio
import json
import subprocess
from ipaddress import IPv4Address

from aiohttp import web
from pathlib import Path
from typing import Awaitable, Callable, Tuple, Any, List, Generator, Dict
from urllib.parse import urlparse

from models.response import GetNodesResponse
from models.types import NodeState, Node

from yapapi.payload import vm
from golem_core import GolemNode, Payload, commands
from golem_core.default_logger import DefaultLogger
from golem_core.mid import (
    Buffer, Chain, Limit, Map, SimpleScorer,
    default_negotiate, default_create_agreement, default_create_activity
)
from golem_core.low import Activity, Network

from app.models.cluster_node import ClusterNode


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
        self._golem = GolemNode()
        self.HEAD_IP = '192.168.0.2'
        self._demand = None
        self._allocation = None
        self._network = None
        self._connections = {}
        self._worker_nodes = {}
        self._num_workers = None
        self._nodes = {}
        self._cluster_nodes: List[ClusterNode] = []

    def get_nodes_response_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"nodes": [x.get_response_dict().dict() for x in self._cluster_nodes]}

    @property
    def golem(self) -> GolemNode:
        """Golem getter"""
        return self._golem

    @property
    def nodes(self) -> dict:
        """Nodes getter"""
        return self._nodes

    async def init(self) -> None:
        self._golem.event_bus.listen(DefaultLogger().on_event)
        self._network = await self._golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
        self._allocation = await self._golem.create_allocation(amount=1, network="goerli")

    @staticmethod
    def get_value_from_dict_or_throw(d, k):
        if k in d:
            return d[k]
        else:
            raise web.HTTPBadRequest(body=f"'{k}' is needed")

    async def create_demand(self, provider_config: dict):
        payload = await self.create_payload(provider_config=provider_config, capabilities=[vm.VM_CAPS_VPN])
        self._demand = await self._golem.create_demand(payload, allocations=[self._allocation])
        await self.create_activities(provider_config=provider_config)
        await self._network.refresh_nodes()
        await self._add_my_key()
        await self._add_other_keys()
        await self._start_head_process()

    async def create_payload(self, provider_config: dict, **kwargs):
        image_hash = self.get_value_from_dict_or_throw(provider_config, 'image_hash')
        result = await vm.repo(image_hash=image_hash, **kwargs)
        return result

    async def create_activities(self, provider_config):
        self._num_workers = provider_config.get('num_workers', 4)
        node_id = 0
        async for activity, ip, uri in Chain(
                self._demand.initial_proposals(),
                # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                Map(default_negotiate),
                Map(default_create_agreement),
                Map(default_create_activity),
                Map(create_ssh_connection(self._network)),
                Limit(self._num_workers + 1),
                Buffer(self._num_workers + 1),
        ):
            cluster_node = ClusterNode(node_id=str(node_id),
                                       activity=activity,
                                       internal_ip=ip)
            self._cluster_nodes.append(cluster_node)

            print(f"Activities: {len(self._cluster_nodes)}/{self._num_workers + 1}")
            self._connections[ip] = uri
            node_id += 1

    @staticmethod
    async def add_authorized_key(activity, key):
        batch = await activity.execute_commands(
            commands.Run('mkdir -p /root/.ssh'),
            commands.Run(f'echo "{key}" >> /root/.ssh/authorized_keys'),
        )
        try:
            await batch.wait(10)
        except Exception:
            print(batch.events)
            raise

    @staticmethod
    async def add_authorized_key_to_local_node():
        pass

    async def _add_my_key(self):
        with open(Path.home() / '.ssh/id_rsa.pub', 'r') as f:
            my_key = f.readline().strip()

        tasks = [self.add_authorized_key(value.activity, my_key) for value in self._cluster_nodes]
        await asyncio.gather(*tasks)

    async def _add_other_keys(self):
        keys = {}
        for cluster_node in self._cluster_nodes:
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
                await self.add_authorized_key(cluster_node.activity, other_activity_key)

    async def _start_head_process(self):
        head_node = next((node for node in self._cluster_nodes if node.internal_ip == self.HEAD_IP), None)
        head_node.state = NodeState.running
        batch = await head_node.activity.execute_commands(
            commands.Run(
                f'ray start --head --include-dashboard=True --node-ip-address {self.HEAD_IP} --disable-usage-stats'),
        )
        await batch.wait(20)

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
