from contextlib import contextmanager
from typing import Iterable, Tuple

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

    @contextmanager
    def _no_progress_bar(self, iterable: Iterable):
        yield iterable

    async def update(self, progress_bar=None) -> Tuple[int, int, int, int]:
        if not progress_bar:
            progress_bar = self._no_progress_bar
        cnt_added = 0
        cnt_updated = 0
        cnt_ignored = 0
        cnt_total = 0
        async with aiohttp.request("get", self.reputation_uri) as response:
            if not response.status == 200:
                raise ReputationUpdaterException(
                    f"Error {response.status} while updating reputation from {self.reputation_uri}"
                )

            data = await response.json()
            with progress_bar(data.get("providers")) as providers:
                for pdata in providers:
                    cnt_total += 1
                    provider_id = pdata.get("providerId")
                    scores = pdata.get("scores")
                    if not (provider_id and scores):
                        cnt_ignored += 1
                    else:
                        network, _ = await m.Network.get_or_create(network_name=self._network)
                        node, _ = await m.Node.get_or_create(node_id=provider_id)
                        node_reputation, created = await m.NodeReputation.get_or_create(
                            node=node, network=network
                        )

                        updated = False
                        success_rate = scores.get("successRate")
                        uptime = scores.get("uptime")
                        if (
                            success_rate is not None
                            and node_reputation.success_rate != success_rate
                        ):
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
