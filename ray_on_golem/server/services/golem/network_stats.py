import logging
from datetime import timedelta
from functools import partial
from typing import Optional

from golem.managers import (
    AddChosenPaymentPlatform,
    BlacklistProviderIdPlugin,
    Buffer,
    DefaultAgreementManager,
    DefaultProposalManager,
    MapScore,
    NegotiatingPlugin,
    PayAllPaymentManager,
    RefreshingDemandManager,
    ScoringBuffer,
)
from golem.node import GolemNode

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.services.golem.provider_data import PROVIDERS_BLACKLIST

logger = logging.getLogger(__name__)


class GolemNetworkStatsService:
    def __init__(self, registry_stats: bool):
        self._registry_stats = registry_stats

        self._demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)

        self._golem: Optional[GolemNode] = None
        self._yagna_appkey: Optional[str] = None
        self._stack: Optional[ManagerStack] = None

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemNetworkStatsService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        logger.info("Starting GolemNetworkStatsService done")

    async def shutdown(self) -> None:
        logger.info("Stopping GolemNetworkStatsService...")

        if self._stack is not None:
            self._stack.stop()
            self._stack = None

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping GolemNetworkStatsService done")

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
        stack.proposal_manager = DefaultProposalManager(
            self._golem,
            stack.demand_manager.get_initial_proposal,
            plugins=(
                BlacklistProviderIdPlugin(PROVIDERS_BLACKLIST.get(network, set())),
                *stack.extra_proposal_plugins,
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(
                        *stack.extra_proposal_scorers,
                        MapScore(partial(self._score_with_provider_data, network=network)),
                    ),
                    update_interval=timedelta(seconds=10),
                ),
                NegotiatingPlugin(
                    proposal_negotiators=(AddChosenPaymentPlatform(),),
                ),
                Buffer(min_size=0, max_size=4, fill_concurrency_size=4),
            ),
        )
        stack.agreement_manager = DefaultAgreementManager(
            self._golem, stack.proposal_manager.get_draft_proposal
        )

        return stack
