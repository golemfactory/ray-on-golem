import logging
from typing import TYPE_CHECKING, Dict, Final, Optional, Sequence, Tuple

from golem.managers.base import ProposalScorer, ProposalScoringResult
from golem.utils.typing import MaybeAwaitable
from tortoise.exceptions import DoesNotExist

from ray_on_golem.reputation import models as m

if TYPE_CHECKING:
    from golem.resources import ProposalData

logger = logging.getLogger(__name__)

PARAM_UPTIME = "uptime"
PARAM_SUCCESS_RATE = "success_rate"
DEFAULT_UPTIME_WEIGHT: Final[float] = 1.0
DEFAULT_SUCCESS_RATE_WEIGHT: Final[float] = 0.5


class ReputationScorer(ProposalScorer):
    def __init__(
        self,
        payment_network: str,
        param_weights: Optional[Dict[str, float]] = None,
        score_range: Tuple[float, float] = (0.0, 1.0),
    ):
        self.payment_network = payment_network
        self.param_weights = param_weights or self._default_weights()
        self.total_weight = sum(self.param_weights.values())
        self.score_range = score_range
        logger.debug(
            f"Initialized {self.__class__.__name__}: "
            "payment_network=%s, weights=%s, score_range=%s",
            self.payment_network,
            self.param_weights,
            self.score_range,
        )

    @staticmethod
    def _default_weights() -> Dict[str, float]:
        return {
            PARAM_UPTIME: DEFAULT_UPTIME_WEIGHT,
            PARAM_SUCCESS_RATE: DEFAULT_SUCCESS_RATE_WEIGHT,
        }

    async def calculate_score(
        self,
        proposal_data: "ProposalData",
    ) -> float:
        provider_id = proposal_data.issuer_id

        try:
            node_reputation = await m.NodeReputation.get_blacklisted(False).get(
                network__network_name=self.payment_network, node__node_id=provider_id
            )
        except DoesNotExist:
            node_reputation = m.NodeReputation()
            logger.debug("Provider `%s` not found. Assuming zero scores.", provider_id)

        score = (
            sum(
                [
                    (getattr(node_reputation, attr) or 0.0) * weight
                    for attr, weight in self.param_weights.items()
                ]
            )
            / self.total_weight
        )
        score_clamped = max(self.score_range[0], min(self.score_range[1], score))

        logger.debug(
            "Provider `%s`'s score: %s (score=%s, node_reputation=%s).",
            provider_id,
            score_clamped,
            score,
            node_reputation,
        )

        return score_clamped

    async def calculate_scores(self, proposals_data: Sequence["ProposalData"]):
        return [await self.calculate_score(proposal_data) for proposal_data in proposals_data]

    def __call__(
        self, proposals_data: Sequence["ProposalData"]
    ) -> MaybeAwaitable[ProposalScoringResult]:
        return self.calculate_scores(proposals_data)
