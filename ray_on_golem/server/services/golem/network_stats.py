import asyncio
import logging
import re
from collections import defaultdict
from datetime import timedelta
from typing import Optional, Sequence

from golem.managers import (
    AddChosenPaymentPlatform,
    BlacklistProviderIdPlugin,
    Buffer,
    DefaultProposalManager,
    NegotiatingPlugin,
    PayAllPaymentManager,
    ProposalManagerPlugin,
    RefreshingDemandManager,
    ScoringBuffer,
)
from golem.managers.base import ProposalNegotiator
from golem.node import GolemNode
from golem.payload import PayloadSyntaxParser
from golem.resources import DemandData, Proposal
from golem.resources.proposal.exceptions import ProposalRejected
from ya_market import ApiException

from ray_on_golem.server.models import CostManagementData, DemandConfigData, NodeConfigData
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.services.golem.provider_data import PROVIDERS_BLACKLIST

logger = logging.getLogger(__name__)


class ProposalCounterPlugin(ProposalManagerPlugin):
    def __init__(self) -> None:
        self._count = 0

    async def get_proposal(self) -> Proposal:
        while True:
            proposal: Proposal = await self._get_proposal()
            self._count += 1
            return proposal


class StatsNegotiatingPlugin(NegotiatingPlugin):
    def __init__(
        self,
        demand_offer_parser: Optional[PayloadSyntaxParser] = None,
        proposal_negotiators: Optional[Sequence[ProposalNegotiator]] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(demand_offer_parser, proposal_negotiators, *args, **kwargs)
        self.fails = defaultdict(int)

    async def get_proposal(self) -> Proposal:
        while True:
            proposal = await self._get_proposal()

            demand_data = await self._get_demand_data_from_proposal(proposal)

            try:
                negotiated_proposal = await self._negotiate_proposal(demand_data, proposal)
                return negotiated_proposal
            except ProposalRejected as err:
                self.fails[err.reason] += 1
            except Exception as err:
                self.fails[str(err)] += 1

    async def _send_demand_proposal(
        self, offer_proposal: Proposal, demand_data: DemandData
    ) -> Proposal:
        try:
            return await offer_proposal.respond(
                demand_data.properties,
                demand_data.constraints,
            )
        except ApiException as e:
            error_msg = re.sub(r"\[.*?\]", "[***]", str(e.body))
            raise RuntimeError(f"Failed to send proposal response! {e.status}: {error_msg}") from e
        except asyncio.TimeoutError as e:
            raise RuntimeError(f"Failed to send proposal response! Request timed out") from e


class StatsPluginFactory:
    _stats_negotiating_plugin: StatsNegotiatingPlugin

    def __init__(self) -> None:
        self._counters = {}

    def print_gathered_stats(self) -> None:
        print("\nProposals count:")
        [print(f"{tag}: {counter._count}") for tag, counter in self._counters.items()]
        print("\nNegotiation errors:")
        [
            print(f"{err}: {count}")
            for err, count in sorted(
                self._stats_negotiating_plugin.fails.items(), key=lambda item: item[1], reverse=True
            )
        ]

    def create_negotiating_plugin(self) -> StatsNegotiatingPlugin:
        self._stats_negotiating_plugin = StatsNegotiatingPlugin(
            proposal_negotiators=(AddChosenPaymentPlatform(),),
        )
        return self._stats_negotiating_plugin

    def create_counter_plugin(self, tag: str) -> ProposalCounterPlugin:
        self._counters[tag] = ProposalCounterPlugin()
        return self._counters[tag]


class GolemNetworkStatsService:
    def __init__(self, registry_stats: bool, run_time_minutes=5) -> None:
        self._registry_stats = registry_stats
        self._run_time = timedelta(minutes=run_time_minutes)

        self._demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)

        self._golem: Optional[GolemNode] = None
        self._yagna_appkey: Optional[str] = None

        self._stats_plugin_factory = StatsPluginFactory()

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemNetworkStatsService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        logger.info("Starting GolemNetworkStatsService done")

    async def shutdown(self) -> None:
        logger.info("Stopping GolemNetworkStatsService...")

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping GolemNetworkStatsService done")

    async def run(self) -> None:
        # FIXME pass args from yaml
        network: str = "goerli"
        # network: str = "polygon"
        budget: int = 1.0
        node_config: NodeConfigData = NodeConfigData(
            demand=DemandConfigData(
                image_tag="blueshade/ray-on-golem:0.2.0-py3.10.13-ray2.7.1",
                capabilities=["vpn", "inet", "manifest-support"],
                min_mem_gib=0.0,
                min_cpu_threads=0,
                min_storage_gib=0.0,
            ),
            cost_management=CostManagementData(
                average_cpu_load=0.8,
                average_duration_minutes=20,
                max_average_usage_cost=1.5,
                max_initial_price=0.5,
                max_cpu_sec_price=0.0005,
                max_duration_sec_price=0.0005,
            ),
        )

        stack = await self._create_stack(node_config, budget, network)
        await stack.start()

        consume_proposals_task = asyncio.create_task(self._consume_draft_proposals(stack))
        await asyncio.wait([consume_proposals_task], timeout=self._run_time.total_seconds())

        consume_proposals_task.cancel()
        await consume_proposals_task

        await stack.stop()
        self._stats_plugin_factory.print_gathered_stats()

    async def _consume_draft_proposals(self, stack: ManagerStack) -> None:
        drafts = []
        try:
            while True:
                draft = await stack.proposal_manager.get_draft_proposal()
                drafts.append(draft)
        except asyncio.CancelledError:
            return
        finally:
            await asyncio.gather(
                # FIXME better reason message
                *[draft.reject(reason="No more needed") for draft in drafts],
                return_exceptions=True,
            )

    async def _create_stack(
        self, node_config: NodeConfigData, budget: float, network: str
    ) -> ManagerStack:
        stack = ManagerStack()

        payload = await self._demand_config_helper.get_payload_from_demand_config(
            node_config.demand
        )

        ManagerStackNodeConfigHelper.apply_cost_management_avg_usage(stack, node_config)
        ManagerStackNodeConfigHelper.apply_cost_management_hard_limits(stack, node_config)

        stack.payment_manager = PayAllPaymentManager(self._golem, budget=budget, network=network)
        stack.demand_manager = RefreshingDemandManager(
            self._golem,
            stack.payment_manager.get_allocation,
            payload,
            demand_expiration_timeout=timedelta(hours=8),
        )

        plugins = [
            self._stats_plugin_factory.create_counter_plugin("Initial"),
            BlacklistProviderIdPlugin(PROVIDERS_BLACKLIST.get(network, set())),
            self._stats_plugin_factory.create_counter_plugin("Not blacklisted"),
        ]

        for idx, plugin in enumerate(stack.extra_proposal_plugins):
            plugins.append(plugin)
            plugins.append(
                self._stats_plugin_factory.create_counter_plugin(
                    f"Passed {plugin.__class__.__name__} {idx + 1}"
                )
            )

        plugins.extend(
            [
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(*stack.extra_proposal_scorers,),
                    update_interval=timedelta(seconds=10),
                ),
                self._stats_plugin_factory.create_counter_plugin("Scored"),
                self._stats_plugin_factory.create_negotiating_plugin(),
                self._stats_plugin_factory.create_counter_plugin("Negotiated"),
                Buffer(min_size=1, max_size=50, fill_concurrency_size=10),
            ]
        )
        stack.proposal_manager = DefaultProposalManager(
            self._golem,
            stack.demand_manager.get_initial_proposal,
            plugins=plugins,
        )

        return stack
