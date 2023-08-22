from typing import Tuple, Any, Awaitable, Callable
from urllib.parse import urlparse

from golem_core.core.activity_api import commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.network_api.resources import Network


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
