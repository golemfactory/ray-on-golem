import logging
from datetime import timedelta

from golem.managers import LinearAverageCostPricing, MapScore, RejectIfCostsExceeds
from golem.managers.proposal.plugins.linear_coeffs import LinearCoeffsCost

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.manager_stack import ManagerStack

logger = logging.getLogger(__name__)


class ManagerStackNodeConfigHelper:
    @staticmethod
    def apply_cost_management_avg_usage(stack: ManagerStack, node_config: NodeConfigData) -> None:
        cost_management = node_config.cost_management

        if cost_management is None or not cost_management.is_average_usage_cost_enabled():
            logger.debug("Cost management based on average usage is not enabled")
            return

        linear_average_cost = LinearAverageCostPricing(
            average_cpu_load=node_config.cost_management.average_cpu_load,
            average_duration=timedelta(
                minutes=node_config.cost_management.average_duration_minutes
            ),
        )

        stack.extra_proposal_scorers.append(
            MapScore(linear_average_cost, normalize=True, normalize_flip=True),
        )

        max_average_usage_cost = node_config.cost_management.max_average_usage_cost
        if max_average_usage_cost is not None:
            stack.extra_proposal_plugins.append(
                RejectIfCostsExceeds(max_average_usage_cost, linear_average_cost),
            )
            logger.debug("Cost management based on average usage applied with max limits")
        else:
            logger.debug("Cost management based on average usage applied without max limits")

    @staticmethod
    def apply_cost_management_hard_limits(stack: ManagerStack, node_config: NodeConfigData) -> None:
        # TODO: Consider creating RejectIfCostsExceeds variant for multiple values
        proposal_plugins = []
        field_names = {
            "max_initial_price": "price_initial",
            "max_cpu_sec_price": "price_cpu_sec",
            "max_duration_sec_price": "price_duration_sec",
        }

        for cost_field_name, coef_field_name in field_names.items():
            cost_max_value = getattr(node_config.cost_management, cost_field_name, None)
            if cost_max_value is not None:
                proposal_plugins.append(
                    RejectIfCostsExceeds(cost_max_value, LinearCoeffsCost(coef_field_name)),
                )

        if proposal_plugins:
            stack.extra_proposal_plugins.extend(proposal_plugins)
            logger.debug("Cost management based on max limits applied")
        else:
            logger.debug("Cost management based on max limits is not enabled")
