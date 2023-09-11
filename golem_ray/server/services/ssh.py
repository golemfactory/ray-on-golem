import base64
import json
import logging
from typing import Any, Awaitable, Callable, Tuple
from urllib.parse import urlparse

from golem_core.core.activity_api import BatchError, commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.network_api.resources import Network

from golem_ray.server.settings import TMP_PATH
from golem_ray.utils import get_ssh_key_name, run_subprocess

logger = logging.getLogger(__name__)


class SshService:
    @staticmethod
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
            )

            try:
                await batch.wait(600)
            except BatchError:
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

            batch = await activity.execute_commands(
                commands.Start(),
                commands.Run("echo 'ON_GOLEM_NETWORK=1' >> /etc/environment"),
                commands.Run("hostname '{}'".format(ip.replace(".", "-"))),
                commands.Run("service ssh start"),
            )
            await batch.wait(600)

            #   3.  Create connection uri
            url = network.node._api_config.net_url
            net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
            connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}"

            return activity, ip, connection_uri

        return _create_ssh_connection

    @classmethod
    async def get_or_create_ssh_key(cls, cluster_name: str) -> str:
        ssh_key_path = TMP_PATH / get_ssh_key_name(cluster_name)

        if not ssh_key_path.exists():
            ssh_key_path.parent.mkdir(parents=True, exist_ok=True)

            await run_subprocess(
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(ssh_key_path)
            )

            logger.info(f"Ssh key for cluster '{cluster_name}' created on path '{ssh_key_path}'")

        with ssh_key_path.open("r") as f:
            return str(f.read())
