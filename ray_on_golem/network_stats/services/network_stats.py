import asyncio
import logging
import re
from collections import defaultdict
from datetime import timedelta
from typing import Dict, Optional, Sequence

from golem.managers import (
    BlacklistProviderIdPlugin,
    DefaultPaymentManager,
    DefaultProposalManager,
    NegotiatingPlugin,
    PaymentPlatformNegotiator,
    ProposalBuffer,
    ProposalManagerPlugin,
    ProposalScoringBuffer,
)
from golem.managers.base import (
    ManagerPluginException,
    PaymentManager,
    ProposalNegotiator,
    ProposalScorer,
)
from golem.node import GolemNode
from golem.resources import DemandData, Proposal
from golem.resources.proposal.exceptions import ProposalRejected
from ya_market import ApiException

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.golem import DEFAULT_DEMAND_LIFETIME
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack

from ray_on_golem.server.services.reputation.plugins import ProviderBlacklistPlugin

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
        proposal_negotiators: Optional[Sequence[ProposalNegotiator]] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(proposal_negotiators, *args, **kwargs)
        self.fails = defaultdict(int)

    async def get_proposal(self) -> Proposal:
        while True:
            proposal = await self._get_proposal()
            demand_data = await proposal.demand.get_demand_data()

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
            raise ManagerPluginException(
                f"Failed to send proposal response! {e.status}: {error_msg}"
            ) from e
        except asyncio.TimeoutError as e:
            raise ManagerPluginException(
                f"Failed to send proposal response! Request timed out"
            ) from e


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
            proposal_negotiators=(PaymentPlatformNegotiator(),),
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

        self._payment_manager: Optional[PaymentManager] = None

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

    async def run(self, config: Dict, node_type: str, duration_minutes: int) -> None:
        provider_parameters: Dict = config["provider"]["parameters"]

        payment_network: str = provider_parameters["payment_network"]
        payment_driver: str = provider_parameters["payment_driver"]
        total_budget: float = provider_parameters["total_budget"]
        node_config = NodeConfigData(**config["available_node_types"][node_type]["node_config"])

        is_head_node = node_type == config.get("head_node_type")

        stack = await self._create_stack(
            node_config=node_config,
            total_budget=total_budget,
            payment_network=payment_network,
            payment_driver=payment_driver,
            is_head_node=is_head_node,
        )
        await stack.start()

        print(
            "Gathering stats data for {} minutes for `{}`{}...".format(
                duration_minutes, node_type, " (head node)" if is_head_node else ""
            )
        )
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
            await self._payment_manager.stop()
            self._payment_manager = None
            print("Gathering stats data done")
            self._stats_plugin_factory.print_gathered_stats()

    async def _consume_draft_proposals(self, stack: ManagerStack) -> None:
        drafts = []
        try:
            while True:
                draft = await stack._managers[-1].get_draft_proposal()
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
        self,
        node_config: NodeConfigData,
        total_budget: float,
        payment_network: str,
        payment_driver: str,
        is_head_node: bool,
    ) -> ManagerStack:
        if not self._payment_manager:
            self._payment_manager = DefaultPaymentManager(
                self._golem, budget=total_budget, network=payment_network, driver=payment_driver
            )
            await self._payment_manager.start()

        stack = ManagerStack()
        extra_proposal_plugins: Dict[str, ProposalManagerPlugin] = {}
        extra_proposal_scorers: Dict[str, ProposalScorer] = {}

        payloads = await self._demand_config_helper.get_payloads_from_demand_config(
            node_config.demand
        )

        ManagerStackNodeConfigHelper.apply_budget_control_expected_usage(
            extra_proposal_plugins, extra_proposal_scorers, node_config
        )
        ManagerStackNodeConfigHelper.apply_budget_control_hard_limits(
            extra_proposal_plugins, node_config
        )

        demand_manager = ManagerStackNodeConfigHelper.prepare_demand_manager_for_node_type(
            stack,
            payloads,
            DEFAULT_DEMAND_LIFETIME,
            node_config,
            is_head_node,
            self._golem,
            self._payment_manager,
        )

        plugins = [
            self._stats_plugin_factory.create_counter_plugin("Initial"),
            ProviderBlacklistPlugin(payment_network),
            self._stats_plugin_factory.create_counter_plugin("Not blacklisted"),
        ]

        for plugin_tag, plugin in extra_proposal_plugins.items():
            plugins.append(plugin)
            plugins.append(self._stats_plugin_factory.create_counter_plugin(f"Passed {plugin_tag}"))

        plugins.extend(
            [
                ProposalScoringBuffer(
                    min_size=500,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(*extra_proposal_scorers.values(),),
                    scoring_debounce=timedelta(seconds=10),
                ),
                self._stats_plugin_factory.create_counter_plugin("Negotiation initialized"),
                self._stats_plugin_factory.create_negotiating_plugin(),
                self._stats_plugin_factory.create_counter_plugin("Negotiated successfully"),
                ProposalBuffer(min_size=800, max_size=1000, fill_concurrency_size=16),
            ]
        )
        stack.add_manager(
            DefaultProposalManager(
                self._golem,
                demand_manager.get_initial_proposal,
                plugins=plugins,
            )
        )

        return stack
