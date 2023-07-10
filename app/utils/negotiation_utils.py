import asyncio
from datetime import timedelta
from random import random

from golem_core.core.market_api.pipeline import default_negotiate


async def negotiate(proposal):
    return await asyncio.wait_for(default_negotiate(proposal), timeout=10)


async def bestprice_score(proposal):
    properties = proposal.data.properties
    if properties['golem.com.pricing.model'] != 'linear':
        return None

    coeffs = properties['golem.com.pricing.model.linear.coeffs']
    return 1 - (coeffs[0] + coeffs[1])


async def random_score(proposal):
    return random()


STRATEGY_SCORING_FUNCTION = {"bestprice": bestprice_score, "random": random_score}
DEFAULT_SCORING_STRATEGY = "bestprice"
DEFAULT_CONNECTION_TIMEOUT = timedelta(minutes=5)
