import asyncio
import hashlib
import os
from asyncio.subprocess import Process
from collections import deque
from datetime import timedelta
from pathlib import Path
from shlex import quote
from typing import Dict, Optional

from aiohttp.web_runner import GracefulExit

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.settings import SSH_SERVER_ALIVE_COUNT_MAX, SSH_SERVER_ALIVE_INTERVAL


async def run_subprocess(
    *args,
    stderr=asyncio.subprocess.DEVNULL,
    stdout=asyncio.subprocess.DEVNULL,
    detach=False,
) -> Process:
    process = await asyncio.create_subprocess_exec(
        *args,
        stderr=stderr,
        stdout=stdout,
        start_new_session=detach,
    )

    return process


async def run_subprocess_output(*args, timeout: Optional[timedelta] = None) -> bytes:
    process = await run_subprocess(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout.total_seconds() if timeout else None,
        )
    except asyncio.TimeoutError as e:
        if process.returncode is None:
            process.kill()
            await process.wait()

        raise RayOnGolemError(f"Process could not finish in timeout of {timeout}!") from e

    if process.returncode != 0:
        raise RayOnGolemError(
            f"Process exited with code `{process.returncode}`!\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )

    return stdout


def are_dicts_equal(dict1: Dict, dict2: Dict) -> bool:
    for key in dict1.keys():
        if key in dict2:
            if dict1[key] != dict2[key]:
                return False

    return True


def is_running_on_golem_network() -> bool:
    """Detect if this code is being executed inside a VM on a provider node."""
    return os.getenv("ON_GOLEM_NETWORK") is not None


def get_default_ssh_key_name(cluster_name: str) -> str:
    return "ray_on_golem_rsa_{}".format(hashlib.md5(cluster_name.encode()).hexdigest()[:10])


def get_ssh_command(
    ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
) -> str:
    proxy_command_str = f"ProxyCommand={ssh_proxy_command}"
    ssh_user_str = f"{ssh_user}@{ip}"

    return " ".join(
        [
            "ssh",
            "-o StrictHostKeyChecking=no",
            "-o UserKnownHostsFile=/dev/null",
            "-o PasswordAuthentication=no",
            f"-o ServerAliveInterval={SSH_SERVER_ALIVE_INTERVAL}",
            f"-o ServerAliveCountMax={SSH_SERVER_ALIVE_COUNT_MAX}",
            f"-o {quote(proxy_command_str)}",
            f"-i {quote(str(ssh_private_key_path))}" if ssh_private_key_path else "",
            quote(ssh_user_str),
        ]
    )


def raise_graceful_exit() -> None:
    raise GracefulExit()


def get_last_lines_from_file(file_path: Path, max_lines: int) -> str:
    with file_path.open() as file:
        return "".join(deque(file, max_lines))
