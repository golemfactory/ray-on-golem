from contextlib import contextmanager
from typing import Iterable, Tuple

import aiohttp
from yarl import URL

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.reputation import models as m

REPUTATION_SYSTEM_URI = URL("https://reputation.dev-test.golem.network/v1/")
REPUTATION_SYSTEM_PROVIDER_SCORES = "providers/scores"


class ReputationUpdaterException(RayOnGolemError):
    ...


class ReputationUpdater:
    """Simple service updating the reputation data from the remote Reputation System."""

    def __init__(self, network: str = "polygon"):
        self._network = network
        self.reputation_uri = (
            REPUTATION_SYSTEM_URI / REPUTATION_SYSTEM_PROVIDER_SCORES % {"network": self._network}
        )

    @contextmanager
    def _no_progress_bar(self, iterable: Iterable):
        """emulate click's progress bar interface without an actual progress bar."""
        yield iterable

    async def get_reputation_data(self):
        """Download the reputation data from the Reputation System endpoint."""
        async with aiohttp.request("get", self.reputation_uri) as response:
            if response.status != 200:
                raise ReputationUpdaterException(
                    f"Error {response.status} while updating reputation from {self.reputation_uri}"
                )

            return await response.json()

    async def update(self, progress_bar=None) -> Tuple[int, int, int, int]:
        """Perform the update."""
        if not progress_bar:
            progress_bar = self._no_progress_bar

        data = await self.get_reputation_data()

        cnt_added = cnt_updated = cnt_ignored = cnt_total = 0

        with progress_bar(data.get("providers")) as providers:
            for pdata in providers:
                cnt_total += 1
                provider_id = pdata.get("providerId")
                scores = pdata.get("scores")

                if not (provider_id and scores):
                    cnt_ignored += 1
                    continue

                network, _ = await m.Network.get_or_create(network_name=self._network)
                node, _ = await m.Node.get_or_create(node_id=provider_id)
                node_reputation, created = await m.NodeReputation.get_or_create(
                    node=node, network=network
                )

                updated = False
                success_rate = scores.get("successRate")
                uptime = scores.get("uptime")
                if success_rate is not None and node_reputation.success_rate != success_rate:
                    node_reputation.success_rate = success_rate
                    updated = True
                if uptime is not None and node_reputation.uptime != uptime:
                    node_reputation.uptime = uptime
                    updated = True

                if updated:
                    await node_reputation.save()

                if created:
                    cnt_added += 1
                elif updated:
                    cnt_updated += 1

        return cnt_added, cnt_updated, cnt_ignored, cnt_total
