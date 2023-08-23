from typing import Any, Awaitable, Callable, Tuple
from urllib.parse import urlparse

from golem_core.core.activity_api import commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.network_api.resources import Network
from yapapi.contrib.service.socket_proxy import ProxyServer


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
                commands.Run("service ssh start"),
                # commands.Run('ssh -R "*:3001:127.0.0.1:6379" proxy@proxy.dev.golem.network'),
            )
            await batch.wait(600)

            #   3.  Create connection uri
            url = network.node._api_config.net_url
            net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
            connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}"

            return activity, ip, connection_uri

        return _create_ssh_connection


class Proxy:
    def __init__(self, ws_url, local_address, local_port, yagna_appkey):
        self.ws_url = ws_url
        self.local_address = local_address
        self.local_port = local_port
        self.yagna_appkey = yagna_appkey

    async def run(self):
        class ProxyServerWrapper(ProxyServer):
            @property
            def app_key(other_self):
                return self.yagna_appkey

            @property
            def instance_ws(other_self):
                return self.ws_url

        proxy_server = ProxyServerWrapper(None, None, None, self.local_address, self.local_port)
        print(f"PROXY STARTED {self.local_address}:{self.local_port} <-> {self.ws_url}")
        await proxy_server.run()
