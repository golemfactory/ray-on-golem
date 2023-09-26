import asyncio
import base64
import json
import logging
import platform
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import async_timeout
import ray
from golem.event_bus import Event
from golem.node import SUBNET, GolemNode
from golem.payload import ManifestVmPayload, constraint, prop
from golem.pipeline import Buffer, Chain, DefaultPaymentHandler, Limit, Map, Sort
from golem.resources import (
    Activity,
    Allocation,
    BatchError,
    Demand,
    Deploy,
    Network,
    Run,
    Start,
    default_create_activity,
    default_create_agreement,
    default_negotiate,
)
from yarl import URL

from ray_on_golem.server.exceptions import (
    CreateActivitiesTimeout,
    RayOnGolemServerError,
    RegistryRequestError,
)
from ray_on_golem.server.models import CreateClusterRequestData, NodeConfigData
from ray_on_golem.server.services.golem.manifest import get_manifest
from ray_on_golem.server.services.golem.repository import PROVIDERS_BLACKLIST, PROVIDERS_WHITELIST

logger = logging.getLogger(__name__)


class GolemService:
    def __init__(self, ray_on_golem_port: int, websocat_path: Path, registry_stats: bool):
        self._ray_on_golem_port = ray_on_golem_port
        self._websocat_path = websocat_path
        self._registry_stats = registry_stats

        self._golem: Optional[GolemNode] = None
        self._demand: Optional[Demand] = None
        self._allocation: Optional[Allocation] = None
        self._network: Optional[Network] = None
        self._payment_manager: Optional[DefaultPaymentHandler] = None
        self._yagna_appkey: Optional[str] = None
        self._lock = asyncio.Lock()
        self._provider_config_network: str = ""

    async def init(self, yagna_appkey: str) -> None:
        logger.info("Starting GolemService...")

        self._golem = GolemNode(app_key=yagna_appkey)
        self._yagna_appkey = yagna_appkey
        await self._golem.start()

        async def on_event(event) -> None:
            logger.debug(f"----- EVENT: {event}")

        await self._golem.event_bus.on(Event, on_event)
        self._network = await self._golem.create_network(
            "192.168.0.1/24"
        )  # will be retrieved from provider_config
        await self._golem.add_to_network(self._network)

        logger.info("Starting GolemService done")

    async def shutdown(self) -> None:
        """
        Terminates all activities and ray on head node.
        Additionally, closes reverse ssh connection from local to proxy.

        :return:
        """
        logger.info("Stopping GolemService...")

        if self._payment_manager is None:
            logger.info(f"No need to wait for invoices, as cluster was not started")
        else:
            await self._payment_manager.terminate_agreements()

            logger.info(f"Waiting for all invoices...")
            await self._payment_manager.wait_for_invoices()
            logger.info(f"Waiting for all invoices done")

        await self._golem.aclose()
        self._golem = None

        logger.info("Stopping GolemService done")

    async def create_cluster(self, provider_config: CreateClusterRequestData):
        """
        Manages creating cluster, creates payload from given data and creates demand basing on payload
        Local node is being created without ray instance.
        :param provider_config: dictionary containing 'num_workers', and 'image_hash' keys
        """
        if self._demand:
            logger.info("Cluster was created already.")
            return

        # TODO remove this attribute and get this information from `self._allocation`
        self._provider_config_network = provider_config.network
        self._allocation = await self._golem.create_allocation(
            amount=provider_config.budget,
            network=provider_config.network,
        )
        self._payment_manager = DefaultPaymentHandler(self._golem, self._allocation)

        payload = await self._create_payload(provider_config.node_config)

        self._demand = await self._golem.create_demand(
            payload,
            allocations=[self._allocation],
            autostart=True,
            expiration=datetime.now(timezone.utc) + timedelta(hours=8),
        )

    async def _create_payload(self, node_config: NodeConfigData) -> ManifestVmPayload:
        """
        Creates payload from given image_hash and parses manifest.json file
        which is then used to create demand in golem network
        :param node_config: dictionary containing image_hash and num_workers
        :return:
        """

        # fix for golem-core-python missing subnet_tag constraint and `debit-notes.accept-timeout?` property
        @dataclass
        class Payload(ManifestVmPayload):
            subnet_constraint: str = constraint("golem.node.debug.subnet", "=", default=SUBNET)
            debit_notes_accept_timeout: int = prop(
                "golem.com.payment.debit-notes.accept-timeout?", default=240
            )

        image_url, image_hash = await self._get_image_url_and_hash(node_config)

        manifest = get_manifest(image_url, image_hash)
        manifest = base64.b64encode(json.dumps(manifest).encode("utf-8")).decode("utf-8")

        params = node_config.dict(exclude={"image_hash", "image_tag"})
        params["manifest"] = manifest

        payload = Payload(**params)

        return payload

    async def _get_image_url_and_hash(self, node_config: NodeConfigData) -> Tuple[URL, str]:
        image_tag = node_config.image_tag
        image_hash = node_config.image_hash

        if image_tag is not None and image_hash is not None:
            raise RayOnGolemServerError(
                "Only one of 'image_tag' and 'image_hash' parameter should be defined!"
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
                    raise RegistryRequestError(f"Image hash {image_hash} does not exist")
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
                    raise RegistryRequestError(f"Image tag '{image_tag}' does not exist")
                else:
                    raise RegistryRequestError("Can't access Golem Registry for image lookup!")

    def get_ssh_proxy_command(self, connection_uri: URL) -> str:
        # Using single quotes for JWT token as double quotes are causing problems with CLI character escaping in ray
        return f"{self._websocat_path} asyncstdio: {connection_uri}/22 --binary -H=Authorization:'Bearer {self._yagna_appkey}'"

    async def create_activities(
        self,
        node_config: Dict[str, Any],
        count: int,
        ssh_user: str,
        ssh_private_key_path: Path,
        ssh_public_key_path: Path,
    ) -> List[Tuple[Activity, str, str]]:
        demand = self._demand  # FIXME: Use demand for proper node_config

        async with self._lock:
            try:
                async with async_timeout.timeout(int(150)):
                    chain = Chain(
                        demand.initial_proposals(),
                        Sort(
                            self._score_proposal_by_blacklist_whitelist,
                            min_elements=2,
                            min_wait=timedelta(seconds=8),
                            max_wait=timedelta(minutes=1),
                        ),
                        Map(self._negotiate),
                        Map(default_create_agreement),
                        Map(default_create_activity),
                        Map(self._deploy_with_vpn_and_start),
                        Map(self._bootstrap_host),
                        Buffer(1),
                        Limit(count),
                    )

                    results = []
                    async for activity, ip in chain:
                        connection_uri = self._get_connection_uri(ip)
                        ssh_proxy_command = self.get_ssh_proxy_command(connection_uri)
                        self._print_ssh_command(
                            ip, ssh_proxy_command, ssh_user, ssh_private_key_path
                        )

                        await self._add_public_ssh_key(activity, ssh_public_key_path)

                        results.append((activity, ip, ssh_proxy_command))

                    await self._network.refresh_nodes()

                    return results

            except asyncio.TimeoutError:
                raise CreateActivitiesTimeout

    @staticmethod
    async def _negotiate(proposal):
        return await asyncio.wait_for(default_negotiate(proposal), timeout=10)

    async def _score_proposal_by_blacklist_whitelist(self, proposal: "Proposal") -> Optional[float]:
        data = await proposal.get_data()
        if data.issuer_id is None:
            return None

        network = self._provider_config_network.lower()
        if data.issuer_id in PROVIDERS_BLACKLIST.get(network, []):
            logger.info("Discarding proposal from blacklisted provider")
            return None

        if data.issuer_id in PROVIDERS_WHITELIST.get(network, []):
            max_score = len(PROVIDERS_WHITELIST.get(network, []))
            provider_seeding = PROVIDERS_WHITELIST.get(network, []).index(data.issuer_id)
            score = float(max_score - provider_seeding)
            logger.info(f"Applying {score} score for proposal from whitelisted provider")
            return score

        logger.info(f"Applying neutral score for proposal from unknown provider")
        return 0.0

    async def _deploy_with_vpn_and_start(self, activity: Activity) -> Tuple[Activity, str]:
        provider_id = activity.parent.parent.data.issuer_id
        assert provider_id is not None  # mypy
        ip = await self._network.create_node(provider_id)

        deploy_args = {"net": [self._network.deploy_args(ip)]}

        batch = await activity.execute_commands(
            Deploy(deploy_args),
            Start(),
        )

        try:
            await batch.wait(600)
        except BatchError:
            # FIXME: image_url should be freely available instead of decoding manifest
            provider_name = activity.parent.parent.data.properties["golem.node.id.name"]
            manifest = json.loads(
                base64.b64decode(
                    activity.parent.parent.demand.data.properties["golem.srv.comp.payload"]
                )
            )
            image_url = manifest["payload"][0]["urls"][0]
            print(
                f"Provider '{provider_name}' deploy failed on image '{image_url}' with batch id: '{batch.id}'"
            )
            raise

        return activity, ip

    async def _bootstrap_host(self, activity: Activity, ip: str) -> Tuple[Activity, str]:
        hostname = ip.replace(".", "-")

        batch = await activity.execute_commands(
            Run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment"),
            Run(f"hostname '{hostname}'"),
            Run(f"echo '{hostname}' > /etc/hostname"),
            Run(f"echo '{ip} {hostname}' >> /etc/hosts"),
            Run("service ssh start"),
        )
        await batch.wait(15)

        return activity, ip

    def _get_connection_uri(self, ip: str) -> URL:
        network_url = URL(self._network.node._api_config.net_url)
        return network_url.with_scheme("ws") / "net" / self._network.id / "tcp" / ip

    def _print_ssh_command(
        self, ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
    ) -> None:
        print(
            f"Connect to {ip} with:\n"
            "ssh "
            "-o StrictHostKeyChecking=no "
            "-o UserKnownHostsFile=/dev/null "
            f'-o "ProxyCommand={ssh_proxy_command}" '
            f"-i {ssh_private_key_path} "
            f"{ssh_user}@{ip}"
        )

    async def _add_public_ssh_key(self, activity: Activity, ssh_public_key_path: Path):
        """
        Add local ssh key to all providers
        """
        if not ssh_public_key_path.exists():
            logger.error(f"{ssh_public_key_path} not exists. SSH connection may fail.")
            return

        # TODO: Use async file handling
        with ssh_public_key_path.open() as f:
            public_ssh_key = f.readline().strip()

        await self._add_authorized_key(activity, public_ssh_key)

    @staticmethod
    async def _add_authorized_key(activity: Activity, key: str) -> None:
        """
        Adds local machine ssh key to providers machine
        :param activity: Activity object from golem
        :param key: Key you want to add to authorized_keys on provider machine
        """
        batch = await activity.execute_commands(
            Run("mkdir -p /root/.ssh"),
            Run(f'echo "{key}" >> /root/.ssh/authorized_keys'),
        )
        try:
            await batch.wait(15)
            logger.info("Added local ssh key to provider with id: {}".format(activity.id))
        except Exception:
            print(batch.events)
            raise
