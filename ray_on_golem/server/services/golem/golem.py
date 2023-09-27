import asyncio
import base64
import hashlib
import json
import logging
import platform
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Tuple

import aiohttp
import ray
from golem.managers import (
    ActivityManager,
    AddChosenPaymentPlatform,
    AgreementManager,
    DefaultAgreementManager,
    DefaultProposalManager,
    DemandManager,
    NegotiatingPlugin,
    PayAllPaymentManager,
    PaymentManager,
    ProposalManager,
    RefreshingDemandManager,
    WorkContext,
)
from golem.node import SUBNET, GolemNode
from golem.payload import ManifestVmPayload, Payload, constraint, prop
from golem.resources import Activity, Network
from yarl import URL

from ray_on_golem.server.exceptions import RayOnGolemServerError, RegistryRequestError
from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest

logger = logging.getLogger(__name__)


class ManagerStack:
    def __init__(
        self,
        payment_manager=None,
        demand_manager=None,
        proposal_manager=None,
        agreement_manager=None,
        activity_manager=None,
    ) -> None:
        self.payment_manager: Optional[PaymentManager] = payment_manager
        self.demand_manager: Optional[DemandManager] = demand_manager
        self.proposal_manager: Optional[ProposalManager] = proposal_manager
        self.agreement_manager: Optional[AgreementManager] = agreement_manager
        self.activity_manager: Optional[ActivityManager] = activity_manager

    @property
    def _managers(self):
        return [
            self.payment_manager,
            self.demand_manager,
            self.proposal_manager,
            self.agreement_manager,
            self.activity_manager,
        ]

    async def start(self) -> None:
        logger.info("Starting stack managers...")

        for manager in self._managers:
            if manager is not None:
                await manager.start()

        logger.info("Starting stack managers done")

    async def stop(self) -> None:
        logger.info("Stopping stack managers...")

        for manager in reversed(self._managers):
            if manager is not None:
                try:
                    await manager.stop()
                except Exception:
                    logger.exception(f"{manager} stop failed!")

        logger.info("Stopping stack managers done")


class GolemService:
    def __init__(self, websocat_path: Path, registry_stats: bool):
        self._websocat_path = websocat_path
        self._registry_stats = registry_stats

        self._golem: Optional[GolemNode] = None
        self._network: Optional[Network] = None
        self._yagna_appkey: Optional[str] = None
        self._stacks: Dict[str, ManagerStack] = {}
        self._stacks_locks = defaultdict(asyncio.Lock)

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        self._network = await self._golem.create_network(
            "192.168.0.1/24"
        )  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)

        logger.info("Starting GolemService done")

    async def shutdown(self) -> None:
        logger.info("Stopping GolemService...")

        await asyncio.gather(
            *[self._remove_stack(stack_hash) for stack_hash in self._stacks.keys()]
        )

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping GolemService done")

    # TODO: Remove stack when last activity was terminated instead of relying on self shutdown
    async def _remove_stack(self, stack_hash: str) -> None:
        async with self._stacks_locks[stack_hash]:
            # FIXME make sure to terminate running activities
            await self._stacks[stack_hash].stop()

            del self._stacks[stack_hash]
            del self._stacks_locks[stack_hash]

    async def _get_or_create_stack_from_node_config(
        self, node_config: NodeConfigData
    ) -> ManagerStack:
        stack_hash = self._get_hash_from_node_config(node_config)

        async with self._stacks_locks[stack_hash]:
            stack = self._stacks.get(stack_hash)
            if stack is None:
                logger.info(f"Creating new stack `{stack_hash}`...")

                self._stacks[stack_hash] = stack = await self._create_stack(node_config)
                await stack.start()

                logger.info(f"Creating new stack `{stack_hash}` done")

            return stack

    @staticmethod
    def _get_hash_from_node_config(node_config: NodeConfigData) -> str:
        return hashlib.md5(node_config.json().encode()).hexdigest()

    async def _create_stack(self, node_config: NodeConfigData) -> ManagerStack:
        stack = ManagerStack()

        payload = await self._get_payload_from_node_config(node_config)

        stack.payment_manager = PayAllPaymentManager(self._golem, budget=1)
        stack.demand_manager = RefreshingDemandManager(
            self._golem, stack.payment_manager.get_allocation, payload
        )
        stack.proposal_manager = DefaultProposalManager(
            self._golem,
            stack.demand_manager.get_initial_proposal,
            plugins=[
                NegotiatingPlugin(
                    proposal_negotiators=[
                        AddChosenPaymentPlatform(),
                    ]
                ),
            ],
        )
        stack.agreement_manager = DefaultAgreementManager(
            self._golem, stack.proposal_manager.get_draft_proposal
        )

        return stack

    async def _get_payload_from_node_config(self, node_config: NodeConfigData) -> Payload:
        @dataclass
        class CustomManifestVmPayload(ManifestVmPayload):
            subnet_constraint: str = constraint("golem.node.debug.subnet", "=", default=SUBNET)
            debit_notes_accept_timeout: int = prop(
                "golem.com.payment.debit-notes.accept-timeout?", default=240
            )

        image_url, image_hash = await self._get_image_url_and_hash(node_config)

        manifest = get_manifest(image_url, image_hash)
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = node_config.dict(exclude={"image_hash", "image_tag"})
        params["manifest"] = manifest

        payload = CustomManifestVmPayload(**params)

        return payload

    async def _get_image_url_and_hash(self, node_config: NodeConfigData) -> Tuple[URL, str]:
        image_tag = node_config.image_tag
        image_hash = node_config.image_hash

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

    async def _on_activity_start(self, context: WorkContext, ip: str, ssh_public_key_data: str):
        deploy_args = {"net": [self._network.deploy_args(ip)]}
        hostname = ip.replace(".", "-")
        batch = await context.create_batch()
        batch.deploy(deploy_args)
        batch.start()
        batch.run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        batch.run(f"hostname '{hostname}'")
        batch.run(f"echo '{hostname}' > /etc/hostname")
        batch.run(f"echo '{ip} {hostname}' >> /etc/hosts")
        batch.run("mkdir -p /root/.ssh")
        batch.run(f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys')
        batch.run("service ssh start")
        await batch()

    async def create_activities(
        self,
        node_config: NodeConfigData,
        count: int,
        ssh_public_key: str,
    ) -> AsyncIterator[Tuple[Activity, str, str]]:
        stack = await self._get_or_create_stack_from_node_config(node_config)

        coros = [self._create_activity(stack, ssh_public_key) for _ in range(count)]

        for coro in asyncio.as_completed(coros):
            result = await coro
            await self._network.refresh_nodes()

            yield result

    async def _create_activity(
        self, stack: ManagerStack, public_ssh_key: str
    ) -> Tuple[Activity, str, str]:
        logger.info(f"Creating new activity...")

        agreement = await stack.agreement_manager.get_agreement()
        activity = await agreement.create_activity()
        ip = await self._network.create_node(activity.parent.parent.data.issuer_id)
        connection_uri = self._get_connection_uri(ip)
        ssh_proxy_command = self._get_ssh_proxy_command(connection_uri)

        await self._on_activity_start(WorkContext(activity), ip, public_ssh_key)

        logger.info(f"Creating new activity done with `{activity}` on ip `{ip}`")

        return activity, ip, ssh_proxy_command

    def _get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def _get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"
