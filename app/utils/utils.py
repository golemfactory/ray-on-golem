import base64
import json
import os
import subprocess
from datetime import timedelta
from pathlib import Path
from subprocess import check_output, Popen
from typing import Tuple, Any, Awaitable, Callable
from urllib.parse import urlparse

from golem_core.core.activity_api import commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.network_api.resources import Network

from app.logger import get_logger

YAGNA_APPNAME = 'requestor-mainnet'

logger = get_logger()


def create_reverse_ssh_to_golem_network() -> Popen[bytes] | Popen[str | bytes | Any]:
    process = subprocess.Popen(["ssh", "-R", r"*:3001:127.0.0.1:6379", "proxy@proxy.dev.golem.network"])
    logger.info('Reverse ssh tunnel from 127.0.0.1:6379 to *:3001 created.')

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


async def parse_manifest(image_hash, text=None):
    """Parses manifest file and replaces image_hash used.
       Decoding is needed in order to work.
       :arg image_hash:
       :arg text:
    """
    manifest = open(Path(__file__).parent.parent.parent.joinpath("manifest.json"), "rb").read()
    manifest = (manifest
                .decode('utf-8')
                .replace('{sha3}', image_hash)
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


def get_or_create_yagna_appkey():
    if os.getenv('YAGNA_APPKEY') is None:
        id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))
        yagna_app = next((app for app in id_data if app['name'] == YAGNA_APPNAME), None)
        if yagna_app is None:
            return check_output(["yagna", "app-key", "create", YAGNA_APPNAME]).decode('utf-8').strip('"\n')
        else:
            return yagna_app['key']
    else:
        return os.getenv('YAGNA_APPKEY')
