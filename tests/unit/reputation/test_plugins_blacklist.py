from unittest import mock

import pytest
from golem.resources import Proposal

from ray_on_golem.reputation.plugins import ProviderBlacklistPlugin
from tests.factories.golem.resources.proposal import ProposalGenerator


@pytest.mark.parametrize(
    "proposal_factory_kwargs, blacklisted, expected_num_rejects, expected_return_type",
    (
        (({"initial": True},), True, 0, type(None)),
        (({"initial": True}, {"initial": False}), True, 1, type(None)),
        (({},), False, 0, Proposal),
        (({"initial": True},), False, 0, Proposal),
    ),
)
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
