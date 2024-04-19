import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, TypeVar

from golem.managers import (
    AgreementManager,
    DefaultAgreementManager,
    DefaultProposalManager,
    Manager,
    MidAgreementPaymentsNegotiator,
    NegotiatingPlugin,
    PaymentManager,
    PaymentPlatformNegotiator,
    ProposalBuffer,
    ProposalManagerPlugin,
    ProposalScorer,
    ProposalScoringBuffer,
    RandomScore,
)
from golem.node import GolemNode
from golem.payload import PaymentInfo
from golem.resources import Agreement, Proposal

from ray_on_golem.reputation.plugins import ProviderBlacklistPlugin, ReputationScorer
from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper

TManager = TypeVar("TManager", bound=Manager)

DEFAULT_DEMAND_LIFETIME = timedelta(hours=8)
DEFAULT_LONG_RUNNING_DEMAND_LIFETIME = timedelta(days=365)
DEFAULT_DEBIT_NOTE_INTERVAL = timedelta(minutes=3)
DEFAULT_DEBIT_NOTES_ACCEPT_TIMEOUT = timedelta(minutes=4)
DEFAULT_PROPOSAL_RESPONSE_TIMEOUT = timedelta(seconds=30)

EXPIRATION_TIME_FACTOR = 0.8

logger = logging.getLogger(__name__)


class ManagerStack:
    def __init__(self) -> None:
        self._managers = []
        self._agreement_manager: Optional[AgreementManager] = None

    def add_manager(self, manager: TManager) -> TManager:
        self._managers.append(manager)

        if isinstance(manager, AgreementManager):
            self._agreement_manager = manager

        return manager

    async def start(self) -> None:
        logger.info("Starting stack managers...")

        for manager in self._managers:
            if manager is not None:
                await manager.start()

        logger.info("Starting stack managers done")

    async def stop(self) -> None:
        logger.info("Stopping stack managers...")

        for manager in reversed(self._managers):
            if manager is not None:
                try:
                    await manager.stop()
                except Exception:
                    logger.exception(f"{manager} stop failed!")

        logger.info("Stopping stack managers done")

    async def get_agreement(self) -> Agreement:
        return await self._agreement_manager.get_agreement()

    @classmethod
    async def create(
        cls,
        node_config: NodeConfigData,
        payment_network: str,
        is_head_node: bool,
        payment_manager: PaymentManager,
        demand_config_helper: DemandConfigHelper,
        golem: GolemNode,
    ) -> "ManagerStack":
        stack = cls()
        extra_proposal_plugins: Dict[str, ProposalManagerPlugin] = {}
        extra_proposal_scorers: Dict[str, ProposalScorer] = {}

        payloads = await demand_config_helper.get_payloads_from_demand_config(node_config.demand)
        demand_lifetime = DEFAULT_DEMAND_LIFETIME

        ManagerStackNodeConfigHelper.apply_budget_control_expected_usage(
            extra_proposal_plugins, extra_proposal_scorers, node_config
        )
        ManagerStackNodeConfigHelper.apply_budget_control_hard_limits(
            extra_proposal_plugins, node_config
        )
        ManagerStackNodeConfigHelper.apply_priority_head_node_scoring(
            extra_proposal_scorers, node_config
        )

        proposal_negotiators = [PaymentPlatformNegotiator()]
        if node_config.budget_control.payment_interval_hours is not None:
            logger.debug(
                "Adding mid agreement payments based on given payment_interval: %s",
                node_config.budget_control.payment_interval_hours,
            )

            minimal_payment_timeout = timedelta(
                hours=node_config.budget_control.payment_interval_hours.minimal
            )
            optimal_payment_timeout = timedelta(
                hours=node_config.budget_control.payment_interval_hours.optimal
            )

            payloads.append(
                PaymentInfo(
                    debit_notes_accept_timeout=int(
                        DEFAULT_DEBIT_NOTES_ACCEPT_TIMEOUT.total_seconds()
                    ),
                    debit_notes_interval=int(DEFAULT_DEBIT_NOTE_INTERVAL.total_seconds()),
                    payment_timeout=int(minimal_payment_timeout.total_seconds()),
                )
            )
            demand_lifetime = DEFAULT_LONG_RUNNING_DEMAND_LIFETIME

            proposal_negotiators.append(
                MidAgreementPaymentsNegotiator(
                    min_debit_note_interval=DEFAULT_DEBIT_NOTE_INTERVAL,
                    optimal_debit_note_interval=DEFAULT_DEBIT_NOTE_INTERVAL,
                    min_payment_timeout=minimal_payment_timeout,
                    optimal_payment_timeout=optimal_payment_timeout,
                )
            )

        demand_manager = stack.add_manager(
            ManagerStackNodeConfigHelper.prepare_demand_manager_for_node_type(
                stack,
                payloads,
                demand_lifetime,
                node_config,
                is_head_node,
                golem,
                payment_manager,
            )
        )

        proposal_manager = stack.add_manager(
            DefaultProposalManager(
                golem,
                demand_manager.get_initial_proposal,
                plugins=(
                    ProviderBlacklistPlugin(payment_network),
                    *extra_proposal_plugins.values(),
                    ProposalScoringBuffer(
                        min_size=50,
                        max_size=1000,
                        fill_at_start=True,
                        proposal_scorers=(
                            *extra_proposal_scorers.values(),
                            ReputationScorer(payment_network),
                            (0.1, RandomScore()),
                        ),
                        scoring_debounce=timedelta(seconds=10),
                        get_expiration_func=cls._get_proposal_expiration,
                    ),
                    NegotiatingPlugin(
                        proposal_negotiators=proposal_negotiators,
                        proposal_response_timeout=DEFAULT_PROPOSAL_RESPONSE_TIMEOUT,
                    ),
                    ProposalBuffer(
                        min_size=0,
                        max_size=4,
                        fill_concurrency_size=4,
                        get_expiration_func=cls._get_proposal_expiration,
                    ),
                ),
            )
        )
        stack.add_manager(DefaultAgreementManager(golem, proposal_manager.get_draft_proposal))

        return stack

    @staticmethod
    async def _get_proposal_expiration(proposal: Proposal) -> timedelta:
        return (
            await proposal.get_expiration_date() - datetime.now(timezone.utc)
        ) * EXPIRATION_TIME_FACTOR
