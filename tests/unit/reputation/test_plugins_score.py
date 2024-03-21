from unittest import mock

import pytest
from tortoise.exceptions import DoesNotExist

from ray_on_golem.reputation.models import NodeReputation
from ray_on_golem.reputation.plugins.score import ReputationScorer


class MockReputationQuerySet:
    def __init__(self, return_value: NodeReputation):
        self.return_value = return_value

    async def get(self, *_, **__):
        return self.return_value


def mock_node_reputation(**kwargs):
    return MockReputationQuerySet(NodeReputation(**kwargs))


@pytest.mark.parametrize(
    "node_reputation, min_score, max_score, side_effect, expected_score",
    (
        # regular scores
        (mock_node_reputation(uptime=0.0, success_rate=0.0), 0.0, 1.0, None, 0.0),
        (mock_node_reputation(uptime=1.0, success_rate=1.0), 0.0, 1.0, None, 1.0),
        # modified min/max
        (mock_node_reputation(uptime=0.0, success_rate=0.0), 0.5, 1.0, None, 0.5),
        (mock_node_reputation(uptime=1.0, success_rate=1.0), 0.0, 0.5, None, 0.5),
        # weights
        (mock_node_reputation(uptime=1.0, success_rate=0.0), 0.0, 1.0, None, 2 / 3),
        (mock_node_reputation(uptime=0.0, success_rate=1.0), 0.0, 1.0, None, 1 / 3),
        # zero score when not found
        (None, 0.0, 1.0, DoesNotExist(), 0.0),
    ),
)
@pytest.mark.asyncio
async def test_reputation_scorer(
    node_reputation, min_score, max_score, side_effect, expected_score
):
    scorer = ReputationScorer("some-network", min_score=min_score, max_score=max_score)
    with mock.patch(
        "ray_on_golem.reputation.models.NodeReputation.get_blacklisted",
        mock.Mock(return_value=node_reputation, side_effect=side_effect),
    ):
        score = await scorer([mock.Mock()])
        assert score == [expected_score]
