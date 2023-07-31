import base64
import os
from asyncio import subprocess
from asyncio.subprocess import Process
from datetime import timedelta
from pathlib import Path
from typing import Tuple, Any, Awaitable, Callable
from urllib.parse import urlparse

from golem_core.core.activity_api import commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.network_api.resources import Network

from golem_ray.server.logger import get_logger

YAGNA_APPNAME = 'requestor-mainnet'

logger = get_logger()


async def create_reverse_ssh_to_golem_network() -> Process:
    process = await subprocess.create_subprocess_shell(
        rf"ssh -N -R *:{os.getenv('SSH_TUNNEL_PORT')}:127.0.0.1:6379 proxy@proxy.dev.golem.network")
    logger.info(f'Reverse ssh tunnel from 127.0.0.1:6379 to *:{os.getenv("SSH_TUNNEL_PORT")} created.')

    return process


def create_ssh_connection(network: Network) -> Callable[[Activity], Awaitable[Tuple[str, str]]]:
    async def _create_ssh_connection(activity: Activity) -> Tuple[Activity, Any, str]:
        #   1.  Create node
        provider_id = activity.parent.parent.data.issuer_id
        assert provider_id is not None  # mypy
        ip = await network.create_node(provider_id)

        #   2.  Run commands
        deploy_args = {"net": [network.deploy_args(ip)]}

        batch = await activity.execute_commands(
            commands.Deploy(deploy_args),
            commands.Start(),
            commands.Run('service ssh start'),
            # commands.Run('ssh -R "*:3001:127.0.0.1:6379" proxy@proxy.dev.golem.network'),
        )
        await batch.wait(600)

        #   3.  Create connection uri
        url = network.node._api_config.net_url
        net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
        connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}"

        return activity, ip, connection_uri

    return _create_ssh_connection


async def parse_manifest(image_hash: str, ssh_tunnel_port: str, text=None):
    """Parses manifest file and replaces image_hash used.
       Decoding is needed in order to work.
       :arg image_hash:
       :arg text:
    """
    with open(Path(__file__).parent.parent.parent.parent.joinpath("manifest.json"), "rb") as manifest:
        manifest = manifest.read()
        manifest = (manifest
                    .decode('utf-8')
                    .replace('{IMAGE_HASH}', image_hash)
                    .replace('{SSH_TUNNEL_PORT}', ssh_tunnel_port)
                    )
        manifest = base64.b64encode(manifest.encode('utf-8')).decode("utf-8")

        params = {
            "manifest": manifest,
            "capabilities": ['vpn', 'inet', 'manifest-support'],
            "min_mem_gib": 0,
            "min_cpu_threads": 0,
            "min_storage_gib": 0,
        }
        # strategy = DEFAULT_SCORING_STRATEGY
        # connection_timeout = DEFAULT_CONNECTION_TIMEOUT
        connection_timeout = timedelta(seconds=150)
        offer_scorer = None
        payload = ManifestVmPayload(**params)

        return payload, offer_scorer, connection_timeout


