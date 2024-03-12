import aiohttp
from ray_on_golem.server.services.reputation import models as m

REPUTATION_SYSTEM_URI = "https://reputation.dev-test.golem.network/v1/"
REPUTATION_SYSTEM_PROVIDER_SCORES = "providers/scores"


class ReputationUpdaterException(Exception):
    ...


class ReputationUpdater:
    def __init__(self, network: str = "polygon"):
        self._network = network

    @property
    def reputation_uri(self):
        return f"{REPUTATION_SYSTEM_URI}{REPUTATION_SYSTEM_PROVIDER_SCORES}?network={self._network}"

    async def update(self):
        async with aiohttp.request("get", self.reputation_uri) as response:
            if not response.status == 200:
                raise ReputationUpdaterException(
                    f"Error {response.status} while updating reputation from {self.reputation_uri}")

            data = await response.json()
            for pdata in data.get("providers"):
                print(pdata)
