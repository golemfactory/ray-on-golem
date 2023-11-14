import base64
import json
import logging
from dataclasses import dataclass
from typing import Tuple

import aiohttp
from golem.node import SUBNET
from golem.payload import ManifestVmPayload, Payload, RepositoryVmPayload, constraint, prop
from yarl import URL

from ray_on_golem.server.exceptions import RayOnGolemServerError, RegistryRequestError
from ray_on_golem.server.models import DemandConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest

logger = logging.getLogger(__name__)


class DemandConfigHelper:
    def __init__(self, registry_stats: bool):
        self._registry_stats = registry_stats

    async def get_payload_from_demand_config(self, demand_config: DemandConfigData) -> Payload:
        image_url, image_hash = await self._get_image_url_and_hash(demand_config)
        if not demand_config.outbound_urls:
            return await self._get_repository_payload(demand_config, image_url, image_hash)

        if "manifest-support" not in demand_config.capabilities:
            demand_config.capabilities.append("manifest-support")
        return await self._get_manifest_payload(demand_config, image_url, image_hash)

    async def _get_repository_payload(
        self, demand_config: DemandConfigData, image_url: URL, image_hash: str
    ) -> Payload:
        @dataclass
        class CustomRepositoryVmPayload(RepositoryVmPayload):
            subnet_constraint: str = constraint("golem.node.debug.subnet", "=", default=SUBNET)
            debit_notes_accept_timeout: int = prop(
                "golem.com.payment.debit-notes.accept-timeout?", default=240
            )

        params = demand_config.dict(exclude={"image_hash", "image_tag", "outbound_urls"})
        params["image_hash"] = image_hash
        params["image_url"] = image_url
        return CustomRepositoryVmPayload(**params)

    async def _get_manifest_payload(
        self, demand_config: DemandConfigData, image_url: URL, image_hash: str
    ) -> Payload:
        @dataclass
        class CustomManifestVmPayload(ManifestVmPayload):
            subnet_constraint: str = constraint("golem.node.debug.subnet", "=", default=SUBNET)
            debit_notes_accept_timeout: int = prop(
                "golem.com.payment.debit-notes.accept-timeout?", default=240
            )

        manifest = get_manifest(
            image_url,
            image_hash,
            list(set([url.scheme for url in demand_config.outbound_urls])),
            demand_config.outbound_urls,
        )
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = demand_config.dict(exclude={"image_hash", "image_tag", "outbound_urls"})
        params["manifest"] = manifest
        return CustomManifestVmPayload(**params)

    async def _get_image_url_and_hash(self, demand_config: DemandConfigData) -> Tuple[URL, str]:
        image_tag = demand_config.image_tag
        image_hash = demand_config.image_hash

        if image_tag is not None and image_hash is not None:
            raise RayOnGolemServerError(
                "Only one of `image_tag` and `image_hash` parameters should be defined!"
            )

        if image_tag is None and image_hash is None:
            raise RayOnGolemServerError(
                "One of `image_tag` and `image_hash` parameters has to be defined!"
            )

        if image_hash is not None:
            image_url = await self._get_image_url_from_hash(image_hash)
            return image_url, image_hash

        if image_tag is not None:
            return await self._get_image_url_and_hash_from_tag(image_tag)

    async def _get_image_url_from_hash(self, image_hash: str) -> URL:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"hash": image_hash, "count": str(self._registry_stats).lower()},
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return URL(response_data["http"])
                elif response.status == 404:
                    raise RegistryRequestError(f"Image hash `{image_hash}` does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")

    async def _get_image_url_and_hash_from_tag(self, image_tag: str) -> Tuple[URL, str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.golem.network/v1/image/info",
                params={"tag": image_tag, "count": str(self._registry_stats).lower()},
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data["http"], response_data["sha3"]
                elif response.status == 404:
                    raise RegistryRequestError(f"Image tag `{image_tag}` does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")
