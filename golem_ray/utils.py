from ast import Tuple
import asyncio

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
