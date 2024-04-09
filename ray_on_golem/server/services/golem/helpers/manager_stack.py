import logging
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Dict, List, Optional

from golem.managers import (
    AggregatingDemandManager,
    DemandManager,
    LinearCoeffsCost,
    LinearPerCpuAverageCostPricing,
    MapScore,
    PaymentManager,
    ProposalManagerPlugin,
    ProposalScorer,
    RefreshingDemandManager,
    RejectIfCostsExceeds,
)
from golem.node import GolemNode
from golem.payload import Payload
from golem.resources import ProposalData

from ray_on_golem.server.models import NodeConfigData

if TYPE_CHECKING:
    from ray_on_golem.server.services.golem.manager_stack import ManagerStack

logger = logging.getLogger(__name__)

HEAD_NODE_EXTRA_SCORE = 100


class ManagerStackNodeConfigHelper:
    @staticmethod
    def apply_budget_control_expected_usage(
        extra_proposal_plugins: Dict[str, ProposalManagerPlugin],
        extra_proposal_scorers: Dict[str, ProposalScorer],
        node_config: NodeConfigData,
    ) -> None:
        per_cpu_expected_usage = node_config.budget_control.per_cpu_expected_usage

        if per_cpu_expected_usage is None:
            logger.debug("Budget control based on per cpu expected usage is not enabled")
            return

        linear_per_cpu_average_cost = LinearPerCpuAverageCostPricing(
            average_cpu_load=per_cpu_expected_usage.cpu_load,
            average_duration=timedelta(hours=per_cpu_expected_usage.duration_hours),
        )

        extra_proposal_scorers["Sort by linear per cpu average cost"] = MapScore(
            linear_per_cpu_average_cost, normalize=True, normalize_flip=True
        )

        max_cost = per_cpu_expected_usage.max_cost
        if max_cost is not None:
            extra_proposal_plugins[
                f"Reject if per cpu expected cost exceeds `max_cost` = {max_cost}"
            ] = RejectIfCostsExceeds(max_cost, linear_per_cpu_average_cost)
            logger.debug("Budget control based on per cpu expected usage applied with max limits")
        else:
            logger.debug(
                "Budget control based on per cpu expected usage applied without max limits"
            )

    @staticmethod
    def apply_budget_control_hard_limits(
        extra_proposal_plugins: Dict[str, ProposalManagerPlugin], node_config: NodeConfigData
    ) -> None:
        # TODO: Consider creating RejectIfCostsExceeds variant for multiple values
        proposal_plugins = {}
        budget_control = node_config.budget_control

        if budget_control.max_start_price is not None:
            proposal_plugins[
                f"Reject if start price exceeds `max_start_price` = {budget_control.max_start_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_start_price, LinearCoeffsCost("price_initial")
            )

        if budget_control.max_cpu_per_hour_price is not None:
            proposal_plugins[
                f"Reject if cpu hour price exceeds `max_cpu_hour_price` = {budget_control.max_cpu_per_hour_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_cpu_per_hour_price / 3600, LinearCoeffsCost("price_cpu_sec")
            )

        if budget_control.max_env_per_hour_price is not None:
            proposal_plugins[
                f"Reject if env per hour price exceeds `max_env_per_hour_price` = {budget_control.max_env_per_hour_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_env_per_hour_price / 3600,
                LinearCoeffsCost("price_duration_sec"),
            )

        if proposal_plugins:
            extra_proposal_plugins.update(proposal_plugins)
            logger.debug("Budget control based on max limits applied")
        else:
            logger.debug("Budget control based on max limits is not enabled")

    @classmethod
    def apply_priority_head_node_scoring(
        cls,
        extra_proposal_scorers: Dict[str, ProposalScorer],
        node_config: NodeConfigData,
    ):
        if not node_config.priority_head_subnet_tag:
            return

        extra_proposal_scorers["Extra score for priority head node"] = MapScore(
            partial(
                cls._score_suggested_heads,
                priority_head_subnet_tag=node_config.priority_head_subnet_tag,
            )
        )

    @staticmethod
    def _score_suggested_heads(
        proposal_data: ProposalData, priority_head_subnet_tag: Optional[str]
    ) -> Optional[float]:
        add_scoring = priority_head_subnet_tag and (
            proposal_data.properties.get("golem.node.debug.subnet") == priority_head_subnet_tag
        )

        return HEAD_NODE_EXTRA_SCORE if add_scoring else 0

    @staticmethod
    def prepare_demand_manager_for_node_type(
        stack: "ManagerStack",
        payloads: List[Payload],
        demand_lifetime: timedelta,
        node_config: NodeConfigData,
        is_head_node: bool,
        golem_node: GolemNode,
        payment_manager: PaymentManager,
    ) -> DemandManager:
        demand_manager = stack.add_manager(
            RefreshingDemandManager(
                golem_node,
                payment_manager.get_allocation,
                payloads,
                demand_lifetime=demand_lifetime,
                subnet_tag=node_config.subnet_tag,
            )
        )

        if is_head_node and node_config.priority_head_subnet_tag:
            suggested_heads_demand_manager = stack.add_manager(
                RefreshingDemandManager(
                    golem_node,
                    payment_manager.get_allocation,
                    payloads,
                    demand_lifetime=demand_lifetime,
                    subnet_tag=node_config.priority_head_subnet_tag,
                )
            )

            demand_manager = stack.add_manager(
                AggregatingDemandManager(
                    golem_node,
                    [
                        suggested_heads_demand_manager.get_initial_proposal,
                        demand_manager.get_initial_proposal,
                    ],
                )
            )

        return demand_manager
