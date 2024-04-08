import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Awaitable, Callable, DefaultDict, Dict, Optional, Tuple

from golem.exceptions import GolemException
from golem.managers import (
    DefaultAgreementManager,
    DefaultPaymentManager,
    DefaultProposalManager,
    MidAgreementPaymentsNegotiator,
    NegotiatingPlugin,
    PaymentManager,
    PaymentPlatformNegotiator,
    ProposalBuffer,
    ProposalManagerPlugin,
    ProposalScorer,
    ProposalScoringBuffer,
    RandomScore,
    WorkContext,
)
from golem.managers.base import ManagerException
from golem.node import GolemNode
from golem.payload import PaymentInfo
from golem.resources import Activity, Allocation, AllocationException, Network, Proposal
from golem.utils.asyncio import create_task_with_logging, ensure_cancelled, ensure_cancelled_many
from golem.utils.logging import trace_span
from ya_payment import models
from yarl import URL

from ray_on_golem.reputation.plugins import ProviderBlacklistPlugin, ReputationScorer
from ray_on_golem.server.models import NodeConfigData
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.helpers.manager_stack import ManagerStackNodeConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.settings import YAGNA_PATH
from ray_on_golem.utils import get_ssh_command, run_subprocess_output

logger = logging.getLogger(__name__)

DEFAULT_DEMAND_LIFETIME = timedelta(hours=8)
DEFAULT_LONG_RUNNING_DEMAND_LIFETIME = timedelta(days=365)
DEFAULT_DEBIT_NOTE_INTERVAL = timedelta(minutes=3)
DEFAULT_DEBIT_NOTES_ACCEPT_TIMEOUT = timedelta(minutes=4)
DEFAULT_PROPOSAL_RESPONSE_TIMEOUT = timedelta(seconds=30)
DEFAULT_SSH_SENTRY_TIMEOUT = timedelta(minutes=2)
DEFAULT_MAX_SENTRY_FAILS_COUNT = 3

EXPIRATION_TIME_FACTOR = 0.8


class NoMatchingPlatform(AllocationException):
    ...


# FIXME: Rework this into the golem-core's DefaultPaymentManager and Allocation on yagna 0.16+,
#  as until then there is no api call available to get driver lists and golem-core is api-only
class DeviceListAllocationPaymentManager(DefaultPaymentManager):
    @trace_span(show_arguments=True, show_results=True)
    async def _create_allocation(self, budget: Decimal, network: str, driver: str) -> Allocation:
        output = json.loads(
            await run_subprocess_output(YAGNA_PATH, "payment", "driver", "list", "--json")
        )

        try:
            network_output = output[driver]["networks"][network]
            platform = network_output["tokens"][network_output["default_token"]]
        except KeyError:
            raise NoMatchingPlatform(network, driver)

        timestamp = datetime.now(timezone.utc)
        timeout = timestamp + timedelta(days=365 * 10)

        data = models.Allocation(
            payment_platform=platform,
            total_amount=str(budget),
            timestamp=timestamp,
            timeout=timeout,
            # This will probably be removed one day (consent-related thing)
            make_deposit=False,
            # We must set this here because of the ya_client interface
            allocation_id="",
            spent_amount="",
            remaining_amount="",
        )

        return await Allocation.create(self._golem, data)


class GolemService:
    def __init__(
        self,
        websocat_path: Path,
        registry_stats: bool,
        ssh_sentry_timeout: timedelta = DEFAULT_SSH_SENTRY_TIMEOUT,
    ):
        self._websocat_path = websocat_path

        self._demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)
        self._golem: Optional[GolemNode] = None
        self._network: Optional[Network] = None
        self._yagna_appkey: Optional[str] = None
        self._stacks: Dict[(str, bool), ManagerStack] = {}
        self._stacks_locks: DefaultDict[(str, bool), asyncio.Lock] = defaultdict(asyncio.Lock)
        self._payment_manager: Optional[PaymentManager] = None

        self._ssh_sentry_tasks: Dict[str, asyncio.Task] = {}
        self._ssh_sentry_timeout: timedelta = ssh_sentry_timeout

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        self._network = await self._golem.create_network(
            "192.168.0.1/16"
        )  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)

        logger.info("Starting GolemService done")

    async def shutdown(self) -> None:
        logger.info("Stopping GolemService...")

        await self.clear()

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping GolemService done")

    # FIXME: Remove this method in case of multiple cluster support
    async def clear(self) -> None:
        await ensure_cancelled_many(self._ssh_sentry_tasks.values())
        self._ssh_sentry_tasks.clear()

        await asyncio.gather(
            *[self._remove_stack(stack_hash) for stack_hash in self._stacks.keys()]
        )

        if self._payment_manager:
            await self._payment_manager.stop()
            self._payment_manager = None

    async def _remove_stack(self, stack_hash: str) -> None:
        logger.info(f"Removing stack `{stack_hash}`...")

        async with self._stacks_locks[stack_hash]:
            await self._stacks[stack_hash].stop()

            del self._stacks[stack_hash]
            del self._stacks_locks[stack_hash]

        logger.info(f"Removing stack `{stack_hash}` done")

    async def _get_or_create_stack_from_node_config(
        self,
        node_config: NodeConfigData,
        total_budget: float,
        payment_network: str,
        payment_driver: str,
        node_type: str,
        is_head_node: bool,
    ) -> ManagerStack:
        stack_key = (node_type, is_head_node)

        async with self._stacks_locks[stack_key]:
            stack = self._stacks.get(stack_key)
            if stack is None:
                logger.info(
                    "Creating new stack `{%s}`: {%s}/{%s}, total_budget={%s}",
                    stack_key,
                    payment_driver,
                    payment_network,
                    total_budget,
                )
                self._stacks[stack_key] = stack = await self._create_stack(
                    node_config=node_config,
                    total_budget=total_budget,
                    payment_network=payment_network,
                    payment_driver=payment_driver,
                    is_head_node=is_head_node,
                )
                await stack.start()

                logger.info(f"Creating new stack `{stack_key}` done")

            return stack

    async def _create_stack(
        self,
        node_config: NodeConfigData,
        total_budget: float,
        payment_network: str,
        payment_driver: str,
        is_head_node: bool,
    ) -> ManagerStack:
        if not self._payment_manager:
            self._payment_manager = DeviceListAllocationPaymentManager(
                self._golem, budget=total_budget, network=payment_network, driver=payment_driver
            )
            await self._payment_manager.start()

        stack = ManagerStack()
        extra_proposal_plugins: Dict[str, ProposalManagerPlugin] = {}
        extra_proposal_scorers: Dict[str, ProposalScorer] = {}

        payloads = await self._demand_config_helper.get_payloads_from_demand_config(
            node_config.demand
        )
        demand_lifetime = DEFAULT_DEMAND_LIFETIME

        ManagerStackNodeConfigHelper.apply_budget_control_expected_usage(
            extra_proposal_plugins, extra_proposal_scorers, node_config
        )
        ManagerStackNodeConfigHelper.apply_budget_control_hard_limits(
            extra_proposal_plugins, node_config
        )
        ManagerStackNodeConfigHelper.apply_priority_head_node_scoring(
            extra_proposal_scorers, node_config
        )

        proposal_negotiators = [PaymentPlatformNegotiator()]
        if node_config.budget_control.payment_interval_hours is not None:
            logger.debug(
                "Adding mid agreement payments based on given payment_interval: %s",
                node_config.budget_control.payment_interval_hours,
            )

            minimal_payment_timeout = timedelta(
                hours=node_config.budget_control.payment_interval_hours.minimal
            )
            optimal_payment_timeout = timedelta(
                hours=node_config.budget_control.payment_interval_hours.optimal
            )

            payloads.append(
                PaymentInfo(
                    debit_notes_accept_timeout=int(
                        DEFAULT_DEBIT_NOTES_ACCEPT_TIMEOUT.total_seconds()
                    ),
                    debit_notes_interval=int(DEFAULT_DEBIT_NOTE_INTERVAL.total_seconds()),
                    payment_timeout=int(minimal_payment_timeout.total_seconds()),
                )
            )
            demand_lifetime = DEFAULT_LONG_RUNNING_DEMAND_LIFETIME

            proposal_negotiators.append(
                MidAgreementPaymentsNegotiator(
                    min_debit_note_interval=DEFAULT_DEBIT_NOTE_INTERVAL,
                    optimal_debit_note_interval=DEFAULT_DEBIT_NOTE_INTERVAL,
                    min_payment_timeout=minimal_payment_timeout,
                    optimal_payment_timeout=optimal_payment_timeout,
                )
            )

        demand_manager = ManagerStackNodeConfigHelper.prepare_demand_manager_for_node_type(
            stack,
            payloads,
            demand_lifetime,
            node_config,
            is_head_node,
            self._golem,
            self._payment_manager,
        )

        proposal_manager = stack.add_manager(
            DefaultProposalManager(
                self._golem,
                demand_manager.get_initial_proposal,
                plugins=(
                    ProviderBlacklistPlugin(payment_network),
                    *extra_proposal_plugins.values(),
                    ProposalScoringBuffer(
                        min_size=50,
                        max_size=1000,
                        fill_at_start=True,
                        proposal_scorers=(
                            *extra_proposal_scorers.values(),
                            ReputationScorer(payment_network),
                            (0.1, RandomScore()),
                        ),
                        scoring_debounce=timedelta(seconds=10),
                        get_expiration_func=self._get_proposal_expiration,
                    ),
                    NegotiatingPlugin(
                        proposal_negotiators=proposal_negotiators,
                        proposal_response_timeout=DEFAULT_PROPOSAL_RESPONSE_TIMEOUT,
                    ),
                    ProposalBuffer(
                        min_size=0,
                        max_size=4,
                        fill_concurrency_size=4,
                        get_expiration_func=self._get_proposal_expiration,
                    ),
                ),
            )
        )
        stack.add_manager(DefaultAgreementManager(self._golem, proposal_manager.get_draft_proposal))

        return stack

    async def _get_proposal_expiration(self, proposal: Proposal) -> timedelta:
        return (
            await proposal.get_expiration_date() - datetime.now(timezone.utc)
        ) * EXPIRATION_TIME_FACTOR

    @staticmethod
    async def get_provider_desc(activity: Activity) -> str:
        proposal = activity.agreement.proposal
        return f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"

    async def _start_activity(
        self, context: WorkContext, ip: str, *, add_state_log: Callable[[str], Awaitable[None]]
    ):
        activity = context.activity
        provider_desc = await self.get_provider_desc(activity)

        logger.info(f"Deploying image on {provider_desc}, {ip=}, {activity=}")

        await add_state_log("[4/9] Deploying image...")
        deploy_args = {"net": [self._network.deploy_args(ip)]}
        await context.deploy(deploy_args, timeout=timedelta(minutes=5))

        await add_state_log("[5/9] Starting VM container...")
        logger.info(f"Starting VM container on {provider_desc}, {ip=}, {activity=}")
        await context.start()

    @staticmethod
    async def _run_command(context: WorkContext, cmd: str, timeout: Optional[float] = None):
        result = await context.run(cmd, timeout=timeout)
        await result.wait()
        logger.debug("Command executed: %s: %s", cmd, [e.to_dict() for e in result.events])

    async def _upload_node_configuration(
        self,
        context: WorkContext,
        ip: str,
        ssh_public_key_data: str,
    ):
        provider_desc = await self.get_provider_desc(context.activity)
        logger.info(f"Running initial commands on {provider_desc}, {ip=}, {context.activity=}")
        hostname = ip.replace(".", "-")
        await self._run_command(context, "echo 'ON_GOLEM_NETWORK=1' >> /etc/environment")
        await self._run_command(context, f"echo 'NODE_IP={ip}' >> /etc/environment")
        await self._run_command(context, f"echo '{hostname}' > /etc/hostname")
        await self._run_command(context, f"echo '{ip} {hostname}' >> /etc/hosts")
        await self._run_command(
            context, "mv /root_copy/.bashrc /root_copy/.profile /root 2> /dev/null"
        )

        await self._run_command(context, "mkdir -p /root/.ssh")
        await self._run_command(
            context, f'echo "{ssh_public_key_data}" >> /root/.ssh/authorized_keys'
        )

    async def _start_ssh_server(self, context: WorkContext, ip: str):
        provider_desc = await self.get_provider_desc(context.activity)
        logger.info("Starting ssh service on " f"{provider_desc}, {ip=}, {context.activity=}")
        await self._run_command(context, "service ssh start")

    async def _restart_ssh_server(self, context: WorkContext, ip: str):
        provider_desc = await self.get_provider_desc(context.activity)
        logger.debug(f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=}")
        try:
            await self._run_command(context, "service ssh restart", timeout=120)
        except Exception:
            msg = f"Failed to restart the SSH server {provider_desc}, {ip=}, {context.activity=}"
            logger.warning(msg)
            logger.debug(msg, exc_info=True)
        else:
            logger.debug(
                f"Restarting ssh service on {provider_desc}, {ip=}, {context.activity=} done"
            )

    @staticmethod
    async def _verify_ssh_connection_check(
        activity_id: str,
        provider_desc: str,
        ip: str,
        ssh_proxy_command: str,
        ssh_user: str,
        ssh_private_key_path: Path,
    ):
        ssh_command = (
            f"{get_ssh_command(ip, ssh_proxy_command, ssh_user, ssh_private_key_path)} uptime"
        )
        logger.debug(
            "SSH connection check started on "
            f"{provider_desc}, {ip=}, {activity_id=}: cmd={ssh_command}."
        )
        process = await asyncio.create_subprocess_shell(
            ssh_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        debug_data = f"{provider_desc=}, exitcode={process.returncode}, {stdout=}, {stderr=}"
        logger.debug(debug_data)

        if process.returncode != 0:
            raise Exception(f"SSH connection check failed. {debug_data}")

    async def _sentry_ssh_connection(
        self,
        context: WorkContext,
        ip: str,
        ssh_proxy_command: str,
        ssh_user: str,
        ssh_private_key_path: Path,
    ):
        provider_desc = await self.get_provider_desc(context.activity)

        fails_count = 0
        while True:
            try:
                await self._verify_ssh_connection(
                    context,
                    ip,
                    ssh_proxy_command,
                    ssh_user,
                    ssh_private_key_path,
                )
            except Exception:
                fails_count += 1
                if fails_count >= DEFAULT_MAX_SENTRY_FAILS_COUNT:
                    msg = f"Destroying activity due to no SSH connection to {provider_desc}"
                    logger.warning(msg)
                    logger.debug(msg, exc_info=True)
                    create_task_with_logging(self.stop_activity(context.activity))
                    break

                logger.debug(
                    f"SSH connection to {provider_desc} stopped working. Restarting SSH server",
                    exc_info=True,
                )
                await self._restart_ssh_server(context, ip)
            await asyncio.sleep(self._ssh_sentry_timeout.total_seconds())

    async def _verify_ssh_connection(
        self,
        context: WorkContext,
        ip: str,
        ssh_proxy_command: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        num_retries=3,
        retry_interval=1,
    ) -> None:
        activity = context.activity
        provider_desc = await self.get_provider_desc(context.activity)

        retry = num_retries

        while retry > 0:
            try:
                await self._verify_ssh_connection_check(
                    activity.id,
                    provider_desc,
                    ip,
                    ssh_proxy_command,
                    ssh_user,
                    ssh_private_key_path,
                )
                break
            except Exception as e:
                retry -= 1
                if retry:
                    logger.warning(f"{str(e)}, retrying {retry}...")
                    await asyncio.sleep(retry_interval)
                    continue
                else:
                    raise GolemException("SSH connection check failed!") from e

        logger.info(f"SSH connection check successful on {provider_desc}, {ip=}, {activity=}.")

    async def create_activity(
        self,
        *,
        node_config: NodeConfigData,
        public_ssh_key: str,
        ssh_user: str,
        ssh_private_key_path: Path,
        total_budget: float,
        payment_network: str,
        payment_driver: str,
        add_state_log: Callable[[str], Awaitable[None]],
        node_type: str,
        is_head_node: bool,
    ) -> Tuple[Activity, str, str]:
        stack = await self._get_or_create_stack_from_node_config(
            node_config=node_config,
            total_budget=total_budget,
            payment_network=payment_network,
            payment_driver=payment_driver,
            node_type=node_type,
            is_head_node=is_head_node,
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
            except (ManagerException,):
                raise
            except (GolemException,) as e:
                msg = "Failed to create activity, retrying."
                error = f"{type(e).__module__}.{type(e).__name__}: {e}"
                await add_state_log(f"{msg} {error=}")
                logger.warning(msg)
                logger.debug(msg, exc_info=True)

    async def stop_activity(self, activity: Activity):
        if activity.id in self._ssh_sentry_tasks:
            await ensure_cancelled(self._ssh_sentry_tasks[activity.id])

        provider_desc = await self.get_provider_desc(activity)
        try:
            await activity.destroy()
        except Exception:
            logger.debug(f"Cannot destroy activity {provider_desc}", exc_info=True)

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

        try:
            agreement = await stack._managers[-1].get_agreement()
        except Exception as e:
            logger.error(f"Creating new activity failed with `{e}`")
            raise

        proposal = agreement.proposal
        provider_desc = f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"
        await add_state_log(f"[2/9] Creating activity on provider: {provider_desc}...")
        activity: Activity = await agreement.create_activity()
        try:
            await add_state_log("[3/9] Adding activity to internal VPN...")
            ip = await self._network.create_node(activity.parent.parent.data.issuer_id)
            connection_uri = self._get_connection_uri(ip)
            ssh_proxy_command = self._get_ssh_proxy_command(connection_uri)

            work_context = WorkContext(activity)
            await self._start_activity(work_context, ip, add_state_log=add_state_log)

            await add_state_log("[6/9] Running bootstrap commands...")
            await self._upload_node_configuration(work_context, ip, public_ssh_key)
            await add_state_log("[7/9] Starting ssh service...")
            await self._start_ssh_server(work_context, ip)

            await add_state_log("[8/9] Checking SSH connection...")
            await self._verify_ssh_connection(
                work_context,
                ip,
                ssh_proxy_command,
                ssh_user,
                ssh_private_key_path,
            )

            self._ssh_sentry_tasks[activity.id] = create_task_with_logging(
                self._sentry_ssh_connection(
                    work_context, ip, ssh_proxy_command, ssh_user, ssh_private_key_path
                )
            )

            await self._network.refresh_nodes()
        except Exception as e:
            logger.error(f"Creating new activity failed with `{type(e).__name__}: {e}`")
            await self.stop_activity(activity)
            raise

        await add_state_log(f"[9/9] Activity ready on provider: {provider_desc}")
        logger.info(
            "Creating new activity done on "
            f"{await self.get_provider_desc(activity)}, {ip=}, {activity=}"
        )

        return activity, ip, ssh_proxy_command

    def _get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def _get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for the authentication token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} -v asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"
