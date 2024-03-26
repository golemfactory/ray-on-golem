from unittest import mock

import pytest
from tortoise.exceptions import DoesNotExist

from ray_on_golem.reputation.models import NodeReputation
from ray_on_golem.reputation.plugins.score import PARAM_SUCCESS_RATE, PARAM_UPTIME, ReputationScorer


class MockReputationQuerySet:
    def __init__(self, return_value: NodeReputation):
        self.return_value = return_value

    async def get(self, *_, **__):
        return self.return_value


def mock_node_reputation(**kwargs):
    return MockReputationQuerySet(NodeReputation(**kwargs))


@pytest.mark.parametrize(
    "node_reputation, param_weights, score_range,   side_effect, expected_score",
    (
        # regular scores
        (mock_node_reputation(uptime=0.0, success_rate=0.0), None, (0.0, 1.0), None, 0.0),
        (mock_node_reputation(uptime=1.0, success_rate=1.0), None, (0.0, 1.0), None, 1.0),
        # modified min/max
        (mock_node_reputation(uptime=0.0, success_rate=0.0), None, (0.3, 0.6), None, 0.3),
        (mock_node_reputation(uptime=1.0, success_rate=1.0), None, (0.3, 0.6), None, 0.6),
        # default weights
        (mock_node_reputation(uptime=1.0, success_rate=0.0), None, (0.0, 1.0), None, 2 / 3),
        (mock_node_reputation(uptime=0.0, success_rate=1.0), None, (0.0, 1.0), None, 1 / 3),
        # custom weights
        (
            mock_node_reputation(uptime=1.0, success_rate=0.0),
            {
                PARAM_UPTIME: 1.0,
            },
            (0.0, 1.0),
            None,
            1.0,
        ),
        (
            mock_node_reputation(uptime=1.0, success_rate=0.0),
            {
                PARAM_SUCCESS_RATE: 1.0,
            },
            (0.0, 1.0),
            None,
            0.0,
        ),
        # zero score when not found
        (None, None, (0.0, 1.0), DoesNotExist(), 0.0),
    ),
)
@pytest.mark.asyncio
async def test_reputation_scorer(
    node_reputation, param_weights, score_range, side_effect, expected_score
):
    scorer = ReputationScorer("some-network", param_weights=param_weights, score_range=score_range)
    with mock.patch(
        "ray_on_golem.reputation.models.NodeReputation.get_blacklisted",
        mock.Mock(return_value=node_reputation, side_effect=side_effect),
    ):
        score = await scorer([mock.Mock()])
        assert score == [expected_score]
