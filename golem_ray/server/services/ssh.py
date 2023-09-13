import asyncio
import logging
from asyncio.subprocess import Process
from pathlib import Path
from typing import Optional

from golem_ray.server.settings import TMP_PATH
from golem_ray.utils import get_ssh_key_name, run_subprocess

logger = logging.getLogger(__name__)


class SshService:
    @staticmethod
    async def create_ssh_reverse_tunel(
        remote_host: str,
        port: int,
        *,
        private_key_path: Optional[Path] = None,
        proxy_command: Optional[str] = None,
    ) -> Process:
        command_parts = [
            f"ssh -N -R '*:{port}:127.0.0.1:{port}'",
            "-o StrictHostKeyChecking=no",
            "-o UserKnownHostsFile=/dev/null",
        ]

        if proxy_command is not None:
            command_parts.append(f'-o ProxyCommand="{proxy_command}"')

        if private_key_path is not None:
            command_parts.append(f"-i {private_key_path}")

        command_parts.append(f"root@{remote_host}")

        # FIXME: Use subprocess running from golem-ray's utils
        process = await asyncio.create_subprocess_shell(
            " ".join(command_parts),
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )

        return process

    @staticmethod
    async def get_or_create_ssh_key(cls, cluster_name: str) -> str:
        # FIXME: Make this function more generic / ray-free
        ssh_key_path = TMP_PATH / get_ssh_key_name(cluster_name)

        if not ssh_key_path.exists():
            ssh_key_path.parent.mkdir(parents=True, exist_ok=True)

            await run_subprocess(
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(ssh_key_path)
            )

            logger.info(f"Ssh key for cluster '{cluster_name}' created on path '{ssh_key_path}'")

        # TODO: async file handling
        with ssh_key_path.open("r") as f:
            return str(f.read())
