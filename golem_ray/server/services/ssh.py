import logging
from asyncio import subprocess
from pathlib import Path
from typing import Any, Awaitable, Callable, Tuple
from urllib.parse import urlparse

from golem_core.core.activity_api import commands
from golem_core.core.activity_api.resources import Activity
from golem_core.core.network_api.resources import Network

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

    @classmethod
    async def create_temporary_ssh_key(cls, ssh_key_dir: Path, ssh_key_filename: str):
        await cls._create_temporary_ssh_directory(ssh_key_dir)

        full_path = ssh_key_dir / ssh_key_filename

        if not full_path.exists():
            try:
                result = await subprocess.create_subprocess_shell(
                    f"ssh-keygen -t rsa -b 4096 -N '' -f {full_path}"
                )
                await result.communicate()
                if result.returncode == 0:
                    logger.info(f"Temporary ssh key created at {full_path}")
                    await cls._add_key_to_agent(full_path)
                else:
                    logger.error(f"Failed to create temporary ssh key at {full_path}")
            except Exception as e:
                logger.error(f"Error creating temporary ssh key: {e}")
        else:
            logger.info(f"Temporary ssh key exists at {full_path}")
            await cls._add_key_to_agent(full_path)

    @staticmethod
    async def remove_temporary_ssh_key(ssh_key_dir: Path, ssh_key_filename: str):
        full_path = ssh_key_dir / ssh_key_filename
        full_path_pub = ssh_key_dir / (ssh_key_filename + ".pub")
        result = await subprocess.create_subprocess_shell("ssh-add -d {}".format(str(full_path)))

        await result.communicate()
        if result.returncode == 0:
            logger.info("SSH key removed from ssh-agent")
        else:
            logger.error("Error while removing ssh key from ssh-agent")

        if full_path.exists():
            full_path.unlink()
        if full_path_pub.exists():
            full_path_pub.unlink()

    @staticmethod
    async def _add_key_to_agent(full_path: Path):
        result = await subprocess.create_subprocess_shell("ssh-add {}".format(str(full_path)))

        await result.communicate()
        if result.returncode == 0:
            logger.info("SSH key added to ssh-agent")
        else:
            logger.error("Error while adding ssh key to ssh-agent")

    @staticmethod
    async def _create_temporary_ssh_directory(ssh_key_dir: Path):
        try:
            ssh_key_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Temporary ssh key directory at {ssh_key_dir}")
        except Exception:
            logger.error(f"Error creating temporary ssh key directory at {ssh_key_dir}")
