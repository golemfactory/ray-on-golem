import base64
import json
import logging
from dataclasses import dataclass
from typing import List, Tuple

import aiohttp
from golem.payload import (
    ManifestVmPayload,
    Payload,
    RepositoryVmPayload,
    constraint,
    defaults,
    prop,
)
from yarl import URL

from ray_on_golem.server.exceptions import RayOnGolemServerError, RegistryRequestError
from ray_on_golem.server.models import DemandConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest

logger = logging.getLogger(__name__)


@dataclass
class MaxCpuThreadsPayload(Payload):
    max_cpu_threads: int = constraint(defaults.PROP_INF_CPU_THREADS, "<=", default=None)


@dataclass
class NodeDescriptorPayload(Payload):
    node_descriptor: str = prop("golem.!exp.gap-31.v0.node.descriptor", default=None)


class DemandConfigHelper:
    def __init__(self, registry_stats: bool):
        self._registry_stats = registry_stats

    async def get_payloads_from_demand_config(
        self, demand_config: DemandConfigData
    ) -> List[Payload]:
        payloads = []
        image_url, image_hash = await self._get_image_url_and_hash(demand_config)
        payloads.append(MaxCpuThreadsPayload(max_cpu_threads=demand_config.max_cpu_threads))

        if demand_config.node_descriptor is not None:
            payloads.append(NodeDescriptorPayload(node_descriptor=demand_config.node_descriptor))

        if not demand_config.outbound_urls:
            payloads.append(
                await self._get_repository_payload(demand_config, image_url, image_hash)
            )
            return payloads

        if "manifest-support" not in demand_config.capabilities:
            demand_config.capabilities.append("manifest-support")

        payloads.append(await self._get_manifest_payload(demand_config, image_url, image_hash))
        return payloads

    async def _get_repository_payload(
        self, demand_config: DemandConfigData, image_url: URL, image_hash: str
    ) -> Payload:
        params = demand_config.dict(
            exclude={
                "image_hash",
                "image_tag",
                "outbound_urls",
                "subnet_tag",
                "max_cpu_threads",
                "node_descriptor",
            }
        )
        params["image_hash"] = image_hash
        params["image_url"] = image_url
        return RepositoryVmPayload(**params)

    async def _get_manifest_payload(
        self, demand_config: DemandConfigData, image_url: URL, image_hash: str
    ) -> Payload:
        manifest = get_manifest(
            image_url,
            image_hash,
            list(set([url.scheme for url in demand_config.outbound_urls])),
            demand_config.outbound_urls,
        )
        logger.debug("Generated manifest:  %s", str(manifest))
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = demand_config.dict(
            exclude={
                "image_hash",
                "image_tag",
                "outbound_urls",
                "subnet_tag",
                "max_cpu_threads",
                "node_descriptor",
            }
        )
        params["manifest"] = manifest
        return ManifestVmPayload(**params)

    async def _get_image_url_and_hash(self, demand_config: DemandConfigData) -> Tuple[URL, str]:
        image_tag = demand_config.image_tag
        image_hash = demand_config.image_hash

        if image_tag is not None and image_hash is not None:
            raise RayOnGolemServerError(
                "Either the `image_tag` or `image_hash` is allowed, not both."
            )

        if image_tag is None and image_hash is None:
            raise RayOnGolemServerError("Either the `image_tag` or `image_hash` is required.")

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
