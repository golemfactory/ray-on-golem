import asyncio
import hashlib
import logging
from collections import defaultdict
from datetime import timedelta
from functools import partial
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional, Tuple

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
        self,
        node_config: NodeConfigData,
        total_budget: float,
        payment_network: str,
        subnet_tag: str,
    ) -> ManagerStack:
        stack_hash = self._get_hash_from_node_config(node_config)

        async with self._stacks_locks[stack_hash]:
            stack = self._stacks.get(stack_hash)
            if stack is None:
                logger.info(
                    f"Creating new stack `{stack_hash}`... {total_budget=}, {payment_network=}, {subnet_tag=}"
                )
                self._stacks[stack_hash] = stack = await self._create_stack(
                    node_config, total_budget, payment_network, subnet_tag
                )
                await stack.start()

                logger.info(f"Creating new stack `{stack_hash}` done")

            return stack

    @staticmethod
    def _get_hash_from_node_config(node_config: NodeConfigData) -> str:
        return hashlib.md5(node_config.json().encode()).hexdigest()

    async def _create_stack(
        self,
        node_config: NodeConfigData,
        total_budget: float,
        payment_network: str,
        subnet_tag: str,
    ) -> ManagerStack:
        stack = ManagerStack()

        payloads = await self._demand_config_helper.get_payloads_from_demand_config(
            node_config.demand
        )

        ManagerStackNodeConfigHelper.apply_budget_control_expected_usage(stack, node_config)
        ManagerStackNodeConfigHelper.apply_budget_control_hard_limits(stack, node_config)

        stack.payment_manager = PayAllPaymentManager(
            self._golem, budget=total_budget, network=payment_network
        )
        stack.demand_manager = RefreshingDemandManager(
            self._golem,
            stack.payment_manager.get_allocation,
            payloads,
            demand_lifetime=timedelta(hours=8),
            subnet_tag=subnet_tag,
        )
        stack.proposal_manager = DefaultProposalManager(
            self._golem,
            stack.demand_manager.get_initial_proposal,
            plugins=(
                BlacklistProviderIdPlugin(PROVIDERS_BLACKLIST.get(payment_network, set())),
                *stack.extra_proposal_plugins.values(),
                ScoringBuffer(
                    min_size=50,
                    max_size=1000,
                    fill_at_start=True,
                    proposal_scorers=(
                        *stack.extra_proposal_scorers.values(),
                        MapScore(
                            partial(self._score_with_provider_data, payment_network=payment_network)
                        ),
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
        self, proposal_data: ProposalData, payment_network: str
    ) -> Optional[float]:
        provider_id = proposal_data.issuer_id

        try:
            prescored_providers = PROVIDERS_SCORED[payment_network]
            provider_pos = prescored_providers.index(provider_id)
        except (KeyError, ValueError):
            return 0

        # Gives pre-scored providers from 0.5 to 1.0 score
        return 0.5 + (0.5 * (provider_pos / len(prescored_providers)))

    @staticmethod
    async def _get_provider_desc(context: WorkContext):
        return f"{await context.get_provider_name()} ({await context.get_provider_id()})"

    async def _start_activity(
        self, context: WorkContext, ip: str, *, add_state_log: Callable[[str], Awaitable[None]]
    ):
        activity = context.activity
        provider_desc = await self._get_provider_desc(context)

        logger.info(f"Deploying image on {provider_desc}, {ip=}, {activity=}")

        await add_state_log("[4/9] Deploying image...")
        deploy_args = {"net": [self._network.deploy_args(ip)]}
        await context.deploy(deploy_args, timeout=timedelta(minutes=5))

        await add_state_log("[5/9] Starting activity...")
        logger.info(f"Starting activity on {provider_desc}, {ip=}, {activity=}")
        await context.start()

    async def _upload_node_configuration(
        self,
        context: WorkContext,
        ip: str,
        ssh_public_key_data: str,
        *,
        add_state_log: Callable[[str], Awaitable[None]],
    ):
        provider_desc = await self._get_provider_desc(context)
        logger.info(f"Running initial commands on {provider_desc}, {ip=}, {context.activity=}")
        await add_state_log("[6/9] Running bootstrap commands...")
        hostname = ip.replace(".", "-")
        await context.run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        await context.run(f"echo 'NODE_IP={ip}' >> /etc/environment")
        await context.run(f"hostname '{hostname}'")
        await context.run(f"echo '{hostname}' > /etc/hostname")
        await context.run(f"echo '{ip} {hostname}' >> /etc/hosts")
        await context.run("mkdir -p /root/.ssh")
        await context.run(f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys')

    async def _start_ssh_server(
        self, context: WorkContext, ip: str, *, add_state_log: Callable[[str], Awaitable[None]]
    ):
        provider_desc = await self._get_provider_desc(context)
        logger.info("Starting ssh service on " f"{provider_desc}, {ip=}, {context.activity=}")
        await add_state_log("[7/9] Starting ssh service...")
        await context.run("service ssh start")

    async def _verify_ssh_connection(
        self,
        context: WorkContext,
        ip: str,
        ssh_proxy_command: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        num_retries=3,
        retry_interval=1,
        *,
        add_state_log: Callable[[str], Awaitable[None]],
    ) -> None:
        activity = context.activity
        ssh_command = (
            f"{get_ssh_command(ip, ssh_proxy_command, ssh_user, ssh_private_key_path)} uptime"
        )

        logger.debug(
            "SSH connection check started on "
            f"{await self._get_provider_desc(context)}, {ip=}, {activity=}: cmd={ssh_command}."
        )
        await add_state_log("[8/9] Checking SSH connection...")

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

        logger.info(
            "SSH connection check successful on "
            f"{await self._get_provider_desc(context)}, {ip=}, {activity=}."
        )
        logger.debug(debug_data)

    async def create_activity(
        self,
        *,
        node_config: NodeConfigData,
        public_ssh_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        total_budget: float,
        payment_network: str,
        subnet_tag: str,
        add_state_log: Callable[[str], Awaitable[None]],
    ) -> Tuple[Activity, str, str]:
        stack = await self._get_or_create_stack_from_node_config(
            node_config, total_budget, payment_network, subnet_tag
        )

        while True:
            try:
                return await self._create_activity(
                    stack,
                    public_ssh_key,
                    ssh_user,
                    ssh_private_key_path,
                    add_state_log=add_state_log,
                )
            except RuntimeError:
                raise
            except Exception:
                msg = "Failed to create activity, retrying"
                await add_state_log(msg)
                logger.warning(msg, exc_info=True)

    async def _create_activity(
        self,
        stack: ManagerStack,
        public_ssh_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        *,
        add_state_log: Callable[[str], Awaitable[None]],
    ) -> Tuple[Activity, str, str]:
        logger.info(f"Creating new activity...")

        await add_state_log("[1/9] Getting agreement...")
        agreement = await stack.agreement_manager.get_agreement()

        proposal = agreement.proposal
        provider_desc = f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"
        await add_state_log(f"[2/9] Creating activity on provider: {provider_desc}...")
        activity = await agreement.create_activity()
        try:
            await add_state_log("[3/9] Adding activity to internal VPN...")
            ip = await self._network.create_node(activity.parent.parent.data.issuer_id)
            connection_uri = self._get_connection_uri(ip)
            ssh_proxy_command = self._get_ssh_proxy_command(connection_uri)

            work_context = WorkContext(activity)
            await self._start_activity(work_context, ip, add_state_log=add_state_log)
            await self._upload_node_configuration(
                work_context, ip, public_ssh_key, add_state_log=add_state_log
            )
            await self._start_ssh_server(work_context, ip, add_state_log=add_state_log)

            await self._verify_ssh_connection(
                work_context,
                ip,
                ssh_proxy_command,
                ssh_user,
                ssh_private_key_path,
                add_state_log=add_state_log,
            )

            await self._network.refresh_nodes()
        except Exception:
            await activity.destroy()
            raise

        await add_state_log(f"[9/9] Activity ready on provider: {provider_desc}")
        logger.info(
            "Creating new activity done on "
            f"{await self._get_provider_desc(work_context)}, {ip=}, {activity=}"
        )

        return activity, ip, ssh_proxy_command

    def _get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def _get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"
