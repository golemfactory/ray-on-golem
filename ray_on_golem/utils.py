import asyncio
import hashlib
import os
from asyncio.subprocess import Process
from pathlib import Path
from typing import Dict, Optional

from aiohttp.web_runner import GracefulExit

from ray_on_golem.exceptions import RayOnGolemError


async def run_subprocess(*args) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RayOnGolemError(stderr)

    return stdout


def are_dicts_equal(dict1: Dict, dict2: Dict) -> bool:
    for key in dict1.keys():
        if key in dict2:
            if dict1[key] != dict2[key]:
                return False

    return True


def is_running_on_golem_network() -> bool:
    return os.getenv("ON_GOLEM_NETWORK") is not None


def get_default_ssh_key_name(cluster_name: str) -> str:
    return "ray_on_golem_rsa_{}".format(hashlib.md5(cluster_name.encode()).hexdigest()[:10])


async def start_ssh_reverse_tunel_process(
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

    process = await asyncio.create_subprocess_shell(
        " ".join(command_parts),
        stderr=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
    )

    return process


def raise_graceful_exit() -> None:
    raise GracefulExit()
