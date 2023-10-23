import asyncio
import base64
import hashlib
import json
import logging
import platform
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Tuple

import aiohttp
import ray
from golem.managers import (
    ActivityManager,
    AddChosenPaymentPlatform,
    AgreementManager,
    BlacklistProviderIdPlugin,
    Buffer,
    DefaultAgreementManager,
    DefaultProposalManager,
    DemandManager,
    LinearAverageCostPricing,
    MapScore,
    NegotiatingPlugin,
    PayAllPaymentManager,
    PaymentManager,
    ProposalManager,
    ProposalManagerPlugin,
    ProposalScorer,
    RefreshingDemandManager,
    RejectIfCostsExceeds,
    ScoringBuffer,
    WorkContext,
)
from golem.managers.proposal.plugins.linear_coeffs import LinearCoeffsCost
from golem.node import SUBNET, GolemNode
from golem.payload import ManifestVmPayload, Payload, constraint, prop
from golem.resources import Activity, Network, ProposalData
from pydantic import BaseModel, Field
from yarl import URL

from ray_on_golem.server.exceptions import RayOnGolemServerError, RegistryRequestError
from ray_on_golem.server.models import DemandConfigData, NodeConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest
from ray_on_golem.server.services.golem.provider_data import PROVIDERS_BLACKLIST, PROVIDERS_SCORED

logger = logging.getLogger(__name__)


class ManagerStack(BaseModel):
    payment_manager: Optional[PaymentManager]
    demand_manager: Optional[DemandManager]
    proposal_manager: Optional[ProposalManager]
    agreement_manager: Optional[AgreementManager]
    activity_manager: Optional[ActivityManager]
    extra_proposal_plugins: List[ProposalManagerPlugin] = Field(default_factory=list)
    extra_proposal_scorers: List[ProposalScorer] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

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
        self, node_config: NodeConfigData, budget: float, network: str
    ) -> ManagerStack:
        stack_hash = self._get_hash_from_node_config(node_config)

        async with self._stacks_locks[stack_hash]:
            stack = self._stacks.get(stack_hash)
            if stack is None:
                logger.info(f"Creating new stack `{stack_hash}`...")

                self._stacks[stack_hash] = stack = await self._create_stack(
                    node_config, budget, network
                )
                await stack.start()

                logger.info(f"Creating new stack `{stack_hash}` done")

            return stack

    @staticmethod
    def _get_hash_from_node_config(node_config: NodeConfigData) -> str:
        return hashlib.md5(node_config.json().encode()).hexdigest()

    async def _create_stack(
        self, node_config: NodeConfigData, budget: float, network: str
    ) -> ManagerStack:
        stack = ManagerStack()

        payload = await self._get_payload_from_demand_config(node_config.demand)

        self._apply_cost_management_avg_usage(stack, node_config)
        self._apply_cost_management_hard_limits(stack, node_config)

        stack.payment_manager = PayAllPaymentManager(self._golem, budget=budget, network=network)
        stack.demand_manager = RefreshingDemandManager(
            self._golem,
            stack.payment_manager.get_allocation,
            payload,
            demand_expiration_timeout=timedelta(hours=8),
        )
        stack.proposal_manager = DefaultProposalManager(
            self._golem,
            stack.demand_manager.get_initial_proposal,
            plugins=(
                BlacklistProviderIdPlugin(PROVIDERS_BLACKLIST.get(network, set())),
                *stack.extra_proposal_plugins,
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(
                        *stack.extra_proposal_scorers,
                        MapScore(partial(self._score_with_provider_data, network=network)),
                    ),
                    update_interval=timedelta(seconds=10),
                ),
                NegotiatingPlugin(
                    proposal_negotiators=(AddChosenPaymentPlatform(),),
                ),
                Buffer(min_size=0, max_size=4, fill_concurrency_size=4),
            ),
        )
        stack.agreement_manager = DefaultAgreementManager(
            self._golem, stack.proposal_manager.get_draft_proposal
        )

        return stack

    async def _get_payload_from_demand_config(self, demand_config: DemandConfigData) -> Payload:
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

    def _apply_cost_management_avg_usage(
        self, stack: ManagerStack, node_config: NodeConfigData
    ) -> None:
        cost_management = node_config.cost_management

        if cost_management is None or not cost_management.is_average_usage_cost_enabled():
            logger.debug("Cost management based on average usage is not enabled")
            return

        linear_average_cost = LinearAverageCostPricing(
            average_cpu_load=node_config.cost_management.average_cpu_load,
            average_duration=timedelta(
                minutes=node_config.cost_management.average_duration_minutes
            ),
        )

        stack.extra_proposal_scorers.append(
            MapScore(linear_average_cost, normalize=True, normalize_flip=True),
        )

        max_average_usage_cost = node_config.cost_management.max_average_usage_cost
        if max_average_usage_cost is not None:
            stack.extra_proposal_plugins.append(
                RejectIfCostsExceeds(max_average_usage_cost, linear_average_cost),
            )
            logger.debug("Cost management based on average usage applied with max limits")
        else:
            logger.debug("Cost management based on average usage applied without max limits")

    def _apply_cost_management_hard_limits(
        self, stack: ManagerStack, node_config: NodeConfigData
    ) -> None:
        # TODO: Consider creating RejectIfCostsExceeds variant for multiple values
        proposal_plugins = []
        field_names = {
            "max_initial_price": "price_initial",
            "max_cpu_sec_price": "price_cpu_sec",
            "max_duration_sec_price": "price_duration_sec",
        }

        for cost_field_name, coef_field_name in field_names.items():
            cost_max_value = getattr(node_config.cost_management, cost_field_name, None)
            if cost_max_value is not None:
                proposal_plugins.append(
                    RejectIfCostsExceeds(cost_max_value, LinearCoeffsCost(coef_field_name)),
                )

        if proposal_plugins:
            stack.extra_proposal_plugins.extend(proposal_plugins)
            logger.debug("Cost management based on max limits applied")
        else:
            logger.debug("Cost management based on max limits is not enabled")

    def _score_with_provider_data(
        self, proposal_data: ProposalData, network: str
    ) -> Optional[float]:
        provider_id = proposal_data.issuer_id

        try:
            prescored_providers = PROVIDERS_SCORED[network]
            provider_pos = prescored_providers.index(provider_id)
        except (KeyError, ValueError):
            return 0

        # Gives pre-scored providers from 0.5 to 1.0 score
        return 0.5 + (0.5 * (provider_pos / len(prescored_providers)))

    async def _start_activity(self, context: WorkContext, ip: str):
        logger.info(f"Deploying image on `{context._activity}`")
        deploy_args = {"net": [self._network.deploy_args(ip)]}
        await context.deploy(deploy_args, timeout=timedelta(minutes=5))

        logger.info(f"Starting `{context._activity}`")
        await context.start()

    async def _upload_node_configuration(
        self, context: WorkContext, ip: str, ssh_public_key_data: str
    ):
        logger.info(f"Running initial commands on `{context._activity}`")
        hostname = ip.replace(".", "-")
        await context.run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        await context.run(f"hostname '{hostname}'")
        await context.run(f"echo '{hostname}' > /etc/hostname")
        await context.run(f"echo '{ip} {hostname}' >> /etc/hosts")
        await context.run("mkdir -p /root/.ssh")
        await context.run(f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys')

    async def _start_ssh_server(self, context: WorkContext):
        logger.info(f"Starting ssh service on `{context._activity}`")
        await context.run("service ssh start")

    async def _verify_ssh_connection(
        self,
        activity: Activity,
        ip: str,
        ssh_proxy_command: str,
        ssh_user: str,
        ssh_private_key_path: Path,
    ) -> None:
        ssh_command = self._get_ssh_command(ip, ssh_proxy_command, ssh_user, ssh_private_key_path)

        logger.debug(f"Verifying ssh connection with:\n{ssh_command} uptime")

        process = await asyncio.create_subprocess_shell(
            f"{ssh_command} uptime",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        msg = f"Validation of ssh connection done on {activity}:\n[cmd exited with {process.returncode}]"
        if stdout:
            msg += f" [stdout] {stdout.decode().strip()}"
        if stderr:
            msg += f" [stderr] {stderr.decode().strip()}"

        if process.returncode != 0:
            logger.warning(msg)
            raise Exception(msg)

        logger.info(msg)

    def _get_ssh_command(
        self, ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
    ) -> str:
        return (
            "ssh "
            "-o StrictHostKeyChecking=no "
            "-o UserKnownHostsFile=/dev/null "
            f'-o "ProxyCommand={ssh_proxy_command}" '
            f"-i {ssh_private_key_path} "
            f"{ssh_user}@{ip}"
        )

    async def create_activities(
        self,
        node_config: NodeConfigData,
        count: int,
        ssh_public_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        budget: float,
        network: str,
    ) -> AsyncIterator[Tuple[Activity, str, str]]:
        stack = await self._get_or_create_stack_from_node_config(node_config, budget, network)

        coros = [
            self._create_activity_retry(stack, ssh_public_key, ssh_user, ssh_private_key_path)
            for _ in range(count)
        ]

        for coro in asyncio.as_completed(coros):
            result = await coro
            await self._network.refresh_nodes()

            yield result

    async def _create_activity_retry(
        self,
        stack: ManagerStack,
        public_ssh_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
    ) -> Tuple[Activity, str, str]:
        while True:
            try:
                return await self._create_activity(
                    stack, public_ssh_key, ssh_user, ssh_private_key_path
                )
            except Exception:
                logger.warning("Failed to create activity, retrying", exc_info=True)

    async def _create_activity(
        self,
        stack: ManagerStack,
        public_ssh_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
    ) -> Tuple[Activity, str, str]:
        logger.info(f"Creating new activity...")

        agreement = await stack.agreement_manager.get_agreement()
        activity = await agreement.create_activity()
        try:
            ip = await self._network.create_node(activity.parent.parent.data.issuer_id)
            connection_uri = self._get_connection_uri(ip)
            ssh_proxy_command = self._get_ssh_proxy_command(connection_uri)

            work_context = WorkContext(activity)
            await self._start_activity(work_context, ip)
            await self._upload_node_configuration(work_context, ip, public_ssh_key)
            await self._start_ssh_server(work_context)

            await self._verify_ssh_connection(
                activity, ip, ssh_proxy_command, ssh_user, ssh_private_key_path
            )
        except Exception:
            await activity.destroy()
            raise

        logger.info(f"Creating new activity done with `{activity}` on ip `{ip}`")

        return activity, ip, ssh_proxy_command

    def _get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def _get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"
