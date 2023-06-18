import asyncio
from pathlib import Path
from typing import Awaitable, Callable, Tuple, Any
from urllib.parse import urlparse

from ray.autoscaler.node_provider import NodeProvider

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
    PAYLOAD = None
    NUM_WORKERS = 5
    HEAD_IP = '192.168.0.2'

    def __init__(self, image_hash):
        self.id: int = 0
        self.demand = None
        self.allocation = None
        self.network = None
        self.golem = GolemNode()
        self.golem.event_bus.listen(DefaultLogger().on_event)
        self.PAYLOAD = Payload.from_image_hash(image_hash, capabilities=[vm.VM_CAPS_VPN])
        self.connections = {}
        self.activities = {}
        self.worker_nodes = []

    async def create_cluster(self, provider_config=None, cluster_name=None):
        async with self.golem:
            self.network = await self.golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
            self.allocation = await self.golem.create_allocation(amount=1, network="goerli")
            self.demand = await self.golem.create_demand(self.PAYLOAD, allocations=[self.allocation])

            async for activity, ip, uri in Chain(
                    self.demand.initial_proposals(),
                    # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
                    Map(default_negotiate),
                    Map(default_create_agreement),
                    Map(default_create_activity),
                    Map(create_ssh_connection(self.network)),
                    Limit(self.NUM_WORKERS + 1),
                    Buffer(self.NUM_WORKERS + 1),
            ):
                self.activities[ip] = activity
                print(f"Activities: {len(self.activities)}/{self.NUM_WORKERS + 1}")
                self.connections[ip] = uri

            print("ACTIVITIES DEPLOYED")
            await self.network.refresh_nodes()
            await self.__add_my_key()
            await self.__add_other_keys()
            await self.__start_head_process()

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

        tasks = [self.add_authorized_key(activity, my_key) for activity in self.activities.values()]
        await asyncio.gather(*tasks)

    async def __add_other_keys(self):
        keys = {}
        activities_values = self.activities.values()
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
        batch = await self.activities[self.HEAD_IP].execute_commands(
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
        start_worker_tasks = []
        for ip, activity in self.activities.items():
            if ip != self.HEAD_IP:
                start_worker_tasks.append(self.__start_worker_process(activity))

        if start_worker_tasks:
            await asyncio.gather(*start_worker_tasks)
