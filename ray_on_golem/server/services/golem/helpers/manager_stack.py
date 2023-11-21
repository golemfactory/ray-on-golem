import logging
from datetime import timedelta

from golem.managers import LinearAverageCostPricing, MapScore, RejectIfCostsExceeds
from golem.managers.proposal.plugins.linear_coeffs import LinearCoeffsCost

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.manager_stack import ManagerStack

logger = logging.getLogger(__name__)


class ManagerStackNodeConfigHelper:
    @staticmethod
    def apply_budget_control_avg_usage(stack: ManagerStack, node_config: NodeConfigData) -> None:
        budget_control = node_config.budget_control

        if budget_control is None or not budget_control.is_expected_usage_cost_enabled():
            logger.debug("Budget control based on expected usage is not enabled")
            return

        linear_average_cost = LinearAverageCostPricing(
            expected_cpu_load=node_config.budget_control.expected_cpu_load,
            average_duration=timedelta(
                minutes=node_config.budget_control.expected_duration_minutes
            ),
        )

        stack.extra_proposal_scorers["Sort by linear average cost"] = MapScore(
            linear_average_cost, normalize=True, normalize_flip=True
        )

        max_expected_usage_cost = node_config.budget_control.max_expected_usage_cost
        if max_expected_usage_cost is not None:
            stack.extra_proposal_plugins[
                f"Reject if max_expected_usage_cost exceeds {node_config.budget_control.max_expected_usage_cost}"
            ] = RejectIfCostsExceeds(max_expected_usage_cost, linear_average_cost)
            logger.debug("Budget control based on expected usage applied with max limits")
        else:
            logger.debug("Budget control based on expected usage applied without max limits")

    @staticmethod
    def apply_budget_control_hard_limits(stack: ManagerStack, node_config: NodeConfigData) -> None:
        # TODO: Consider creating RejectIfCostsExceeds variant for multiple values
        proposal_plugins = {}
        field_names = {
            "max_initial_price": "price_initial",
            "max_cpu_sec_price": "price_cpu_sec",
            "max_duration_sec_price": "price_duration_sec",
        }

        for cost_field_name, coef_field_name in field_names.items():
            cost_max_value = getattr(node_config.budget_control, cost_field_name, None)
            if cost_max_value is not None:
                proposal_plugins[
                    f"Reject if {coef_field_name} exceeds {cost_max_value}"
                ] = RejectIfCostsExceeds(cost_max_value, LinearCoeffsCost(coef_field_name))

        if proposal_plugins:
            stack.extra_proposal_plugins.update(proposal_plugins)
            logger.debug("Budget control based on max limits applied")
        else:
            logger.debug("Budget control based on max limits is not enabled")
