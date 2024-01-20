import asyncio
import hashlib
import os
from asyncio.subprocess import Process
from collections import deque
from pathlib import Path
from typing import Dict

from aiohttp.web_runner import GracefulExit

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.settings import TMP_PATH


async def run_subprocess(
    *args, stderr=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL
) -> Process:
    process = await asyncio.create_subprocess_exec(
        *args,
        stderr=stderr,
        stdout=stdout,
        # As this process lifetime will be fully managed, we need to disable signal propagation
        # from parent to child process https://stackoverflow.com/a/5446982/1993670
        preexec_fn=os.setpgrp,
    )

    return process


async def run_subprocess_output(*args) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

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
    return os.getenv("ON_GOLEM_NETWORK") is not None


def get_default_ssh_key_name(cluster_name: str) -> str:
    return "ray_on_golem_rsa_{}".format(hashlib.md5(cluster_name.encode()).hexdigest()[:10])


def raise_graceful_exit() -> None:
    raise GracefulExit()


def get_last_lines_from_file(file_path: Path, max_lines: int) -> str:
    with file_path.open() as file:
        return "".join(deque(file, max_lines))


def prepare_tmp_dir():
    try:
        TMP_PATH.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
