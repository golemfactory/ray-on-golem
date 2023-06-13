from typing import Any

from golem_core import GolemNode
from golem_core.default_logger import DefaultLogger
from golem_core.mid import Chain, Map, default_negotiate, default_create_agreement, default_create_activity, Buffer, \
    Limit
from ray.autoscaler._private.aws.node_provider import (
    AWSNodeProvider,
)  # testing purposes
from ray.autoscaler.node_provider import NodeProvider

from start_ray_cluster import create_ssh_connection


class GolemNodeProvider(NodeProvider):

    # needs yapapi
    # PAYLOAD = Payload.from_image_hash(
    #     "83a7145df831d9b62508a912485d2e9ac03e70df328e7142a899c2bf",
    #     capabilities=[vm.VM_CAPS_VPN],
    # )
    PAYLOAD = None

    def __init__(self, provider_config, cluster_name):
        super().__init__(provider_config, cluster_name)

        self.golem = GolemNode()
        self.golem.event_bus.listen(DefaultLogger().on_event)

        async with self.golem:
            self.network = await self.golem.create_network("192.168.0.1/24")  # will be retrieved from provider_config
            self.allocation = await self.golem.create_allocation(amount=1, network="goerli")
            self.demand = await self.golem.create_demand(self.PAYLOAD, allocations=[self.allocation])

        self.connections = {}
        self.activities = {}

    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, Any] | None:
        activities = {}
        connections = {}
        async for activity, ip, uri in Chain(
            self.demand.initial_proposals(),
            # SimpleScorer(score_proposal, min_proposals=200, max_wait=timedelta(seconds=5)),
            Map(default_negotiate),
            Map(default_create_agreement),
            Map(default_create_activity),
            Map(create_ssh_connection(self.network)),
            Limit(1),  # since we only create one node, Chain is probably not right choice here
            Buffer(1),
        ):
            activities[ip] = activity
            connections[ip] = uri

        self.activities.update(activities)
        self.connections.update(connections)

        print("ACTIVITY DEPLOYED")
        await self.network.refresh_nodes()

        return activities
