import base64
import json
import logging
import platform
from dataclasses import dataclass
from typing import Tuple

import aiohttp
import ray
from golem.node import SUBNET
from golem.payload import ManifestVmPayload, Payload, constraint, prop
from yarl import URL

from ray_on_golem.server.exceptions import RayOnGolemServerError, RegistryRequestError
from ray_on_golem.server.models import DemandConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest

logger = logging.getLogger(__name__)


class DemandConfigHelper:
    def __init__(self, registry_stats: bool):
        self._registry_stats = registry_stats

    async def get_payload_from_demand_config(self, demand_config: DemandConfigData) -> Payload:
        @dataclass
        class CustomManifestVmPayload(ManifestVmPayload):
            subnet_constraint: str = constraint("golem.node.debug.subnet", "=", default=SUBNET)
            debit_notes_accept_timeout: int = prop(
                "golem.com.payment.debit-notes.accept-timeout?", default=240
            )

        image_url, image_hash = await self._get_image_url_and_hash(demand_config)

        manifest = get_manifest(image_url, image_hash)
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = demand_config.dict(exclude={"image_hash", "image_tag"})
        params["manifest"] = manifest

        payload = CustomManifestVmPayload(**params)

        return payload

    async def _get_image_url_and_hash(self, demand_config: DemandConfigData) -> Tuple[URL, str]:
        image_tag = demand_config.image_tag
        image_hash = demand_config.image_hash

        if image_tag is not None and image_hash is not None:
            raise RayOnGolemServerError(
                "Only one of `image_tag` and `image_hash` parameter should be defined!"
            )

        if image_hash is not None:
            image_url = await self._get_image_url_from_hash(image_hash)
            return image_url, image_hash

        if image_tag is None:
            python_version = platform.python_version()
            ray_version = ray.__version__
            image_tag = f"golem/ray-on-golem:py{python_version}-ray{ray_version}"

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
