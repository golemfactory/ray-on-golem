from tortoise.exceptions import DoesNotExist

from typing import Final, Optional, TYPE_CHECKING

from ray_on_golem.server.services.reputation import models as m


if TYPE_CHECKING:
    from golem.resources import ProposalData

DEFAULT_UPTIME_WEIGHT: Final[float] = 1.0
DEFAULT_SUCCESS_RATE_WEIGHT: Final[float] = 0.5

# TODO write a custom scorer plugin, since the golem-core-supplied one doesn't support async callbacks

async def calculate_provider_score(
    proposal_data: ProposalData,
    payment_network: str,
    uptime_weight: float = DEFAULT_UPTIME_WEIGHT,
    success_rate_weight: float = DEFAULT_SUCCESS_RATE_WEIGHT,
) -> float:
    provider_id = proposal_data.issuer_id

    try:
        node_reputation = await m.NodeReputation.get_blacklisted(False).get(network__network_name=payment_network, node__node_id=provider_id)
        uptime = node_reputation.uptime or 0.0
        success_rate = node_reputation.success_rate or 0.0
    except DoesNotExist:
        uptime = 0.0
        success_rate = 0.0

    score = uptime * uptime_weight + success_rate * success_rate_weight / (uptime_weight + success_rate_weight)

    # return score clamped to <0.0, 1.0>
    return max(0.0, min(1.0, score))
