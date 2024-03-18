from typing import Dict, Optional, Sequence
from unittest import mock

import pytest
from golem.resources import Proposal

from ray_on_golem.reputation.plugins import ProviderBlacklistPlugin
from tests.factories.golem.resources.proposal import ProposalFactory


class ProposalGenerator:
    """Generates the required Proposals with specified factory parameters.

    We provide kwargs, not direct Proposal objects to allow passing them as test parameters.
    As initialization of Proposal object requires an asyncio loop to be runnning, we cannot
    do this declaratively.
    """

    def __init__(self, factory_kwargs: Optional[Sequence[Dict]] = None):
        self.proposals = list()
        self.generator = (ProposalFactory(**kwargs) for kwargs in factory_kwargs or (dict(),))

    async def get_proposal(self) -> Proposal:
        proposal = next(self.generator)
        self.proposals.append(proposal)
        return proposal


@pytest.fixture
def proposal_generator(request):
    factory_kwargs: Sequence[Dict] = ({},)
    try:
        factory_kwargs = request.param
    except AttributeError:
        pass
    return ProposalGenerator(factory_kwargs).get_proposal


@pytest.mark.parametrize(
    "proposal_factory_kwargs, blacklisted, expected_num_rejects, expected_return_type",
    (
        (({"initial": True},), True, 0, type(None)),
        (({"initial": True}, {"initial": False}), True, 1, type(None)),
        (({},), False, 0, Proposal),
        (({"initial": True},), False, 0, Proposal),
    ),
)
@pytest.mark.asyncio
async def test_blacklist(
    blacklisted, proposal_factory_kwargs, expected_num_rejects, expected_return_type
):
    with mock.patch(
        "ray_on_golem.reputation.models.NodeReputation.check_blacklisted",
        mock.AsyncMock(return_value=blacklisted),
    ):
        proposal = None
        with mock.patch("golem.resources.Proposal.reject") as reject_mock:
            blacklist = ProviderBlacklistPlugin("some-network")
            blacklist.set_proposal_callback(ProposalGenerator(proposal_factory_kwargs).get_proposal)
            if blacklisted:
                with pytest.raises(RuntimeError, match="StopIteration"):
                    await blacklist.get_proposal()
            else:
                proposal = await blacklist.get_proposal()

            assert isinstance(proposal, expected_return_type)
            assert reject_mock.call_count == expected_num_rejects
