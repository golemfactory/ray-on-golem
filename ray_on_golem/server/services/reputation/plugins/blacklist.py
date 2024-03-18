import logging

from golem.managers import ProposalManagerPlugin
from golem.resources import Proposal

from ray_on_golem.server.services.reputation import models as m

logger = logging.getLogger(__name__)


class ProviderBlacklistPlugin(ProposalManagerPlugin):
    """A proposal manager plugin which rejects providers based on the local blacklist."""

    def __init__(self, payment_network: str):
        self._payment_network = payment_network

    async def get_proposal(self) -> Proposal:
        while True:
            proposal: Proposal = await self._get_proposal()
            proposal_data = await proposal.get_data()
            provider_id = proposal_data.issuer_id

            if not await m.NodeReputation.check_blacklisted(provider_id, self._payment_network):
                return proposal

            if not proposal.initial:
                await proposal.reject(f"Provider: `{provider_id}` is blacklisted")

            logger.debug(
                "Provider `%s` from proposal `%s` is blacklisted, picking a different proposal...",
                provider_id,
                proposal,
            )
