import asyncio
import logging
import re
from collections import defaultdict
from datetime import timedelta
from typing import Dict, Optional, Sequence

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

from ray_on_golem.server.models import NodeConfigData
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


class NetworkStatsService:
    def __init__(self, registry_stats: bool) -> None:
        self._registry_stats = registry_stats

        self._demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)

        self._golem: Optional[GolemNode] = None
        self._yagna_appkey: Optional[str] = None

        self._stats_plugin_factory = StatsPluginFactory()

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting NetworkStatsService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        logger.info("Starting NetworkStatsService done")

    async def shutdown(self) -> None:
        logger.info("Stopping NetworkStatsService...")

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping NetworkStatsService done")

    async def run(self, provider_parameters: Dict, duration_minutes: int) -> None:
        network: str = provider_parameters["network"]
        budget: int = provider_parameters["budget"]
        node_config: NodeConfigData = NodeConfigData(**provider_parameters["node_config"])

        stack = await self._create_stack(node_config, budget, network)
        await stack.start()

        print(f"Gathering stats data for {duration_minutes} minutes...")
        consume_proposals_task = asyncio.create_task(self._consume_draft_proposals(stack))
        try:
            await asyncio.wait(
                [consume_proposals_task],
                timeout=timedelta(minutes=duration_minutes).total_seconds(),
            )
        finally:
            consume_proposals_task.cancel()
            await consume_proposals_task

            await stack.stop()
            print("Gathering stats data done")
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

        for plugin_tag, plugin in stack.extra_proposal_plugins.items():
            plugins.append(plugin)
            plugins.append(self._stats_plugin_factory.create_counter_plugin(f"Passed {plugin_tag}"))

        plugins.extend(
            [
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(*stack.extra_proposal_scorers.values(),),
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
