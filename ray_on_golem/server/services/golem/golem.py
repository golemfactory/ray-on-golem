import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from golem.managers import DefaultPaymentManager
from golem.node import GolemNode
from golem.resources import Allocation, AllocationException, DeployArgsType, Network
from golem.utils.logging import trace_span
from ya_payment import models
from yarl import URL

from ray_on_golem.server.services.golem.helpers import DemandConfigHelper
from ray_on_golem.server.settings import YAGNA_PATH
from ray_on_golem.utils import run_subprocess_output

logger = logging.getLogger(__name__)


class NoMatchingPlatform(AllocationException):
    ...


# FIXME: Rework this into the golem-core's DefaultPaymentManager and Allocation on yagna 0.16+,
#  as until then there is no api call available to get driver lists and golem-core is api-only
class DriverListAllocationPaymentManager(DefaultPaymentManager):
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
    def __init__(self, websocat_path: Path, registry_stats: bool):
        self._websocat_path = websocat_path

        self.golem: Optional[GolemNode] = None
        self.demand_config_helper: DemandConfigHelper = DemandConfigHelper(registry_stats)

        self._network: Optional[Network] = None
        self._yagna_appkey: Optional[str] = None

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemService...")

        self.golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self.golem.start()

        self._network = await self.golem.create_network(
            "192.168.0.1/16"
        )  # will be retrieved from provider_parameters
        await self.golem.add_to_network(self._network)

        logger.info("Starting GolemService done")

    async def stop(self) -> None:
        logger.info("Stopping GolemService...")

        await self.golem.aclose()
        self.golem = None

        logger.info("Stopping GolemService done")

    async def add_provider_to_network(self, provider_id: str) -> str:
        return await self._network.create_node(provider_id)

    async def refresh_network_nodes(self) -> None:
        await self._network.refresh_nodes()

    def get_deploy_args(self, ip: str) -> DeployArgsType:
        return self._network.deploy_args(ip)

    def get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for the authentication token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} -vv asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"
