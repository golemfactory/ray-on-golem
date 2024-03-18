import logging
from typing import TYPE_CHECKING, Final, Sequence

from golem.managers.base import ProposalScorer, ProposalScoringResult
from golem.utils.typing import MaybeAwaitable
from tortoise.exceptions import DoesNotExist

from ray_on_golem.reputation import models as m

if TYPE_CHECKING:
    from golem.resources import ProposalData

logger = logging.getLogger(__name__)

DEFAULT_UPTIME_WEIGHT: Final[float] = 1.0
DEFAULT_SUCCESS_RATE_WEIGHT: Final[float] = 0.5


class ReputationScorer(ProposalScorer):
    def __init__(
        self,
        payment_network: str,
        uptime_weight: float = DEFAULT_UPTIME_WEIGHT,
        success_rate_weight: float = DEFAULT_SUCCESS_RATE_WEIGHT,
        min_score: float = 0.0,
        max_score: float = 1.0,
    ):
        self.payment_network = payment_network
        self.uptime_weight = uptime_weight
        self.success_rate_weight = success_rate_weight
        self.total_weight = self.uptime_weight + self.success_rate_weight
        self.min_score = min_score
        self.max_score = max_score
        logger.debug(
            f"Initialized {self.__class__.__name__}: "
            "payment_network=%s, uptime_weight=%s, "
            "success_rate_weight=%s, min_score=%s, max_score=%s",
            self.payment_network,
            self.uptime_weight,
            self.success_rate_weight,
            self.min_score,
            self.max_score,
        )

    async def calculate_score(
        self,
        proposal_data: "ProposalData",
    ) -> float:
        provider_id = proposal_data.issuer_id

        try:
            node_reputation = await m.NodeReputation.get_blacklisted(False).get(
                network__network_name=self.payment_network, node__node_id=provider_id
            )
            uptime = node_reputation.uptime or 0.0
            success_rate = node_reputation.success_rate or 0.0
        except DoesNotExist:
            uptime = 0.0
            success_rate = 0.0
            logger.debug("Provider `%s` not found. Assuming zero scores.", provider_id)

        score = (
            uptime * self.uptime_weight + success_rate * self.success_rate_weight
        ) / self.total_weight
        score_clamped = max(self.min_score, min(self.max_score, score))

        logger.debug(
            "Provider `%s`'s score: %s (score=%s, uptime=%s, success_rate=%s).",
            provider_id,
            score_clamped,
            score,
            uptime,
            success_rate,
        )

        return score_clamped

    async def calculate_scores(self, proposals_data: Sequence["ProposalData"]):
        return [await self.calculate_score(proposal_data) for proposal_data in proposals_data]

    def __call__(
        self, proposals_data: Sequence["ProposalData"]
    ) -> MaybeAwaitable[ProposalScoringResult]:
        return self.calculate_scores(proposals_data)
