import logging
from datetime import timedelta

from golem.managers import (
    LinearCoeffsCost,
    LinearPerCpuAverageCostPricing,
    MapScore,
    RejectIfCostsExceeds,
)

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.manager_stack import ManagerStack

logger = logging.getLogger(__name__)


class ManagerStackNodeConfigHelper:
    @staticmethod
    def apply_budget_control_expected_usage(
        stack: ManagerStack, node_config: NodeConfigData
    ) -> None:
        per_cpu_expected_usage = node_config.budget_control.per_cpu_expected_usage

        if per_cpu_expected_usage is None:
            logger.debug("Budget control based on per cpu expected usage is not enabled")
            return

        linear_per_cpu_average_cost = LinearPerCpuAverageCostPricing(
            average_cpu_load=per_cpu_expected_usage.cpu_load,
            average_duration=timedelta(hours=per_cpu_expected_usage.duration_hours),
        )

        stack.extra_proposal_scorers["Sort by linear per cpu average cost"] = MapScore(
            linear_per_cpu_average_cost, normalize=True, normalize_flip=True
        )

        max_cost = per_cpu_expected_usage.max_cost
        if max_cost is not None:
            stack.extra_proposal_plugins[
                f"Reject if per cpu expected cost exceeds {max_cost}"
            ] = RejectIfCostsExceeds(max_cost, linear_per_cpu_average_cost)
            logger.debug("Budget control based on per cpu expected usage applied with max limits")
        else:
            logger.debug(
                "Budget control based on per cpu expected usage applied without max limits"
            )

    @staticmethod
    def apply_budget_control_hard_limits(stack: ManagerStack, node_config: NodeConfigData) -> None:
        # TODO: Consider creating RejectIfCostsExceeds variant for multiple values
        proposal_plugins = {}
        budget_control = node_config.budget_control

        if budget_control.max_start_price is not None:
            proposal_plugins[
                f"Reject if start_price exceeds {budget_control.max_start_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_start_price, LinearCoeffsCost("price_initial")
            )

        if budget_control.max_cpu_per_hour_price is not None:
            proposal_plugins[
                f"Reject if cpu_hour_price exceeds {budget_control.max_cpu_per_hour_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_cpu_per_hour_price / 3600, LinearCoeffsCost("price_cpu_sec")
            )

        if budget_control.max_env_per_hour_price is not None:
            proposal_plugins[
                f"Reject if env_per_hour_price exceeds {budget_control.max_env_per_hour_price}"
            ] = RejectIfCostsExceeds(
                budget_control.max_env_per_hour_price / 3600,
                LinearCoeffsCost("price_duration_sec"),
            )

        if proposal_plugins:
            stack.extra_proposal_plugins.update(proposal_plugins)
            logger.debug("Budget control based on max limits applied")
        else:
            logger.debug("Budget control based on max limits is not enabled")
