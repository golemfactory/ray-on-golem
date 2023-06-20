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
        self.golem = GolemNode()
        self._demand = None
        self._allocation = None
        self._network = None
        self._connections = {}
        self._activities = {}
        self._worker_nodes = []

    async def init(self) -> None:
        # await self.golem.__aenter__()
        self.HEAD_IP = '192.168.0.2'
        self.golem.event_bus.listen(DefaultLogger().on_event)
        self._network = await self.golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
        self._allocation = await self.golem.create_allocation(amount=1, network="goerli")

    async def shutdown(self, *exc_info) -> None:
        await self.golem.__aexit__(exc_info)

    @staticmethod
    def get_value_from_dict_or_throw(d, k):
        if k in d:
            return d[k]
        else:
            raise web.HTTPBadRequest(body=f"'{k}' is needed")

    async def create_demand(self, provider_config: dict):
        payload = await self.create_payload(provider_config=provider_config, capabilities=[vm.VM_CAPS_VPN])
        self._demand = await self.golem.create_demand(payload, allocations=[self._allocation])
        await self.create_activities(provider_config=provider_config)
        await self._network.refresh_nodes()
        await self.__add_my_key()
        await self.__add_other_keys()
        await self.__start_head_process()

        return self._activities

    async def create_payload(self, provider_config: dict, **kwargs):
        image_hash = self.get_value_from_dict_or_throw(provider_config, 'image_hash')
        result = await vm.repo(image_hash=image_hash, **kwargs)
        return result

    async def create_activities(self, provider_config):
        num_workers = provider_config.get('num_workers', 4)
        async for activity, ip, uri in Chain(
                self._demand.initial_proposals(),
                # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                Map(default_negotiate),
                Map(default_create_agreement),
                Map(default_create_activity),
                Map(create_ssh_connection(self._network)),
                Limit(num_workers + 1),
                Buffer(num_workers + 1),
        ):
            self._activities[ip] = activity
            print(f"Activities: {len(self._activities)}/{num_workers + 1}")
            self._connections[ip] = uri

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

    async def __add_my_key(self):
        with open(Path.home() / '.ssh/id_rsa.pub', 'r') as f:
            my_key = f.readline().strip()

        tasks = [self.add_authorized_key(activity, my_key) for activity in self._activities.values()]
        await asyncio.gather(*tasks)

    async def __add_other_keys(self):
        keys = {}
        activities_values = self._activities.values()
        for activity in activities_values:
            batch = await activity.execute_commands(
                commands.Run('ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'),
                commands.Run('cat /root/.ssh/id_rsa.pub'),
            )
            await batch.wait()
            key = batch.events[-1].stdout.strip()
            keys[activity] = key

        for activity in activities_values:
            for other_activity in (a for a in activities_values if a is not activity):
                other_activity_key = keys[other_activity]
                await self.add_authorized_key(activity, other_activity_key)

    async def __start_head_process(self):
        batch = await self._activities[self.HEAD_IP].execute_commands(
            commands.Run(
                f'ray start --head --include-dashboard=True --node-ip-address {self.HEAD_IP} --disable-usage-stats'),
        )
        await batch.wait(20)

    async def __start_worker_process(self, activity):
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
        if count + len(self._worker_nodes) > len(self._worker_nodes):
            raise web.HTTPBadRequest(body={"message": "Max workers limit exceeded"})

        start_worker_tasks = []
        for ip, activity in self._activities.items():
            if ip != self.HEAD_IP:
                start_worker_tasks.append(self.__start_worker_process(activity))
                self._worker_nodes.append({"node_ip": ip})

        if start_worker_tasks:
            await asyncio.gather(*start_worker_tasks)
