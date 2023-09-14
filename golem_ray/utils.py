import asyncio
import hashlib
from functools import lru_cache

from yarl import URL

from golem_ray.client.golem_ray_client import GolemRayClient
from golem_ray.exceptions import GolemRayError


async def run_subprocess(*args) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise GolemRayError(stderr)

    return stdout


def get_golem_ray_client_url(port: int) -> URL:
    return URL("http://127.0.0.1").with_port(port)


@lru_cache()
def get_golem_ray_client(port: int) -> GolemRayClient:
    url = get_golem_ray_client_url(port)
    return GolemRayClient(url)


def get_ssh_key_name(cluster_name: str) -> str:
    return "golem_ray_rsa_{}".format(hashlib.md5(cluster_name.encode()).hexdigest()[:10])
