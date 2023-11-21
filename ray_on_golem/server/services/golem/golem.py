import asyncio
import hashlib
import logging
from collections import defaultdict
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Tuple

from golem.managers import (
    AddChosenPaymentPlatform,
    BlacklistProviderIdPlugin,
    Buffer,
    DefaultAgreementManager,
    DefaultProposalManager,
    MapScore,
    NegotiatingPlugin,
    PayAllPaymentManager,
    RefreshingDemandManager,
    ScoringBuffer,
    WorkContext,
)
from golem.node import GolemNode
from golem.resources import Activity, Network, ProposalData
from yarl import URL

from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.services.golem.provider_data import PROVIDERS_BLACKLIST, PROVIDERS_SCORED
from ray_on_golem.server.services.utils import get_ssh_command

logger = logging.getLogger(__name__)


class GolemService:
    def __init__(self, websocat_path: Path, registry_stats: bool):
        self._websocat_path = websocat_path

        self._demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)
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
        self, node_config: NodeConfigData, budget_limit: float, network: str
    ) -> ManagerStack:
        stack_hash = self._get_hash_from_node_config(node_config)

        async with self._stacks_locks[stack_hash]:
            stack = self._stacks.get(stack_hash)
            if stack is None:
                logger.info(f"Creating new stack `{stack_hash}`...")

                self._stacks[stack_hash] = stack = await self._create_stack(
                    node_config, budget_limit, network
                )
                await stack.start()

                logger.info(f"Creating new stack `{stack_hash}` done")

            return stack

    @staticmethod
    def _get_hash_from_node_config(node_config: NodeConfigData) -> str:
        return hashlib.md5(node_config.json().encode()).hexdigest()

    async def _create_stack(
        self, node_config: NodeConfigData, budget_limit: float, network: str
    ) -> ManagerStack:
        stack = ManagerStack()

        payload = await self._demand_config_helper.get_payload_from_demand_config(
            node_config.demand
        )

        ManagerStackNodeConfigHelper.apply_budget_control_avg_usage(stack, node_config)
        ManagerStackNodeConfigHelper.apply_budget_control_hard_limits(stack, node_config)

        stack.payment_manager = PayAllPaymentManager(
            self._golem, budget=budget_limit, network=network
        )
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
                *stack.extra_proposal_plugins.values(),
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(
                        *stack.extra_proposal_scorers.values(),
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
        await context.run(f"echo 'NODE_IP={ip}' >> /etc/environment")
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
        num_retries=3,
        retry_interval=1,
    ) -> None:
        ssh_command = (
            f"{get_ssh_command(ip, ssh_proxy_command, ssh_user, ssh_private_key_path)} uptime"
        )

        logger.debug(f"SSH connection check started on {activity}: cmd={ssh_command}")

        debug_data = ""

        async def check():
            nonlocal debug_data

            process = await asyncio.create_subprocess_shell(
                ssh_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            debug_data = f"{activity=}, exitcode={process.returncode}, {stdout=}, {stderr=}"

            if process.returncode != 0:
                raise Exception(f"SSH connection check failed. {debug_data}")

        retry = num_retries

        while retry > 0:
            try:
                await check()
                break
            except Exception as e:
                retry -= 1
                if retry:
                    logger.warning(f"{str(e)}, retrying {retry}...")
                    await asyncio.sleep(retry_interval)
                    continue
                else:
                    raise

        logger.info(f"SSH connection check successful on {activity}.")
        logger.debug(debug_data)

    async def create_activities(
        self,
        node_config: NodeConfigData,
        count: int,
        ssh_public_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        budget_limit: float,
        network: str,
    ) -> AsyncIterator[Tuple[Activity, str, str]]:
        stack = await self._get_or_create_stack_from_node_config(node_config, budget_limit, network)

        coros = [
            self._create_activity_retry(stack, ssh_public_key, ssh_user, ssh_private_key_path)
            for _ in range(count)
        ]

        for coro in asyncio.as_completed(coros):
            try:
                result = await coro
            except Exception:
                logger.warning("Unable to create activity, abandoning", exc_info=True)
                continue
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
            except RuntimeError:
                raise
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
