import asyncio
import json

from aiohttp import web
from pathlib import Path
from typing import Awaitable, Callable, Tuple, Any
from urllib.parse import urlparse

from yapapi.payload import vm
from golem_core import GolemNode, Payload, commands
from golem_core.default_logger import DefaultLogger
from golem_core.mid import (
    Buffer, Chain, Limit, Map, SimpleScorer,
    default_negotiate, default_create_agreement, default_create_activity
)
from golem_core.low import Activity, Network


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

    @property
    def golem(self) -> GolemNode:
        return self._golem

    async def init(self) -> None:
        # await self.golem.__aenter__()
        self._golem.event_bus.listen(DefaultLogger().on_event)
        self._network = await self._golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
        self._allocation = await self._golem.create_allocation(amount=1, network="goerli")

    async def shutdown(self, *exc_info) -> None:
        await self._golem.__aexit__(exc_info)

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

        return self._nodes

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
            # self._nodes[node_id] = (ip, activity)
            self._nodes[node_id] = {"ip": ip, "activity": activity, "ray": False}
            print(f"Activities: {len(self._nodes)}/{self._num_workers + 1}")
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

    async def _add_my_key(self):
        with open(Path.home() / '.ssh/id_rsa.pub', 'r') as f:
            my_key = f.readline().strip()

        tasks = [self.add_authorized_key(value.get('activity'), my_key) for value in self._nodes.values()]
        await asyncio.gather(*tasks)

    async def _add_other_keys(self):
        keys = {}
        nodes_values = self._nodes.values()
        for node_id, node in self._nodes.items():
            batch = await node.get('activity').execute_commands(
                commands.Run('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'),
                commands.Run('cat /root/.ssh/id_rsa.pub'),
            )
            await batch.wait()
            key = batch.events[-1].stdout.strip()
            keys[node_id] = key

        for node_id, node in self._nodes.items():
            other_activities = ((_id, _node) for _id, _node in self._nodes.items() if _id != node_id)
            # for other_activity in (a.get('activity') for a in nodes_values if
            #                        a.get('ip') is not node.get('ip')):
            for other_activity in other_activities:
                other_activity_key = keys[other_activity[0]]
                await self.add_authorized_key(node.get('activity'), other_activity_key)

    async def _start_head_process(self):
        print(self._nodes)
        head_node = next((obj for obj in self._nodes.values() if obj.get('ip') == self.HEAD_IP), None)
        head_node['type'] = "head"
        head_node['ray'] = True
        batch = await head_node.get('activity').execute_commands(
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
        nodes_with_ray_on_count = sum(obj.get('ray') for obj in self._nodes.values())
        if count + nodes_with_ray_on_count > self._num_workers + 1:
            raise web.HTTPBadRequest(body="Max workers limit exceeded")

        start_worker_tasks = []
        for node in self._nodes.values():
            if node.get('ip') != self.HEAD_IP:
                start_worker_tasks.append(self._start_worker_process(node.get('activity')))
                node['type'] = "worker"
                node['ray'] = True

        if start_worker_tasks:
            await asyncio.gather(*start_worker_tasks)

        return self._nodes

    async def stop_worker(self, node_id: int):
        pass
