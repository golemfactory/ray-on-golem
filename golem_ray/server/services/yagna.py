import asyncio
import json
import logging
from asyncio.subprocess import Process
from pathlib import Path
from typing import Optional

from golem_ray.exceptions import GolemRayError
from golem_ray.server.settings import YAGNA_APPKEY
from golem_ray.utils import run_subprocess

logger = logging.getLogger(__name__)

YAGNA_APPNAME = "golem-ray"


class YagnaServiceError(GolemRayError):
    pass


class YagnaService:
    def __init__(self, yagna_path: Path):
        self._yagna_path = yagna_path

        self.yagna_appkey: Optional[str] = None
        self._yagna_process: Optional[Process] = None

    async def init(self) -> None:
        self.yagna_appkey = await self._get_or_create_yagna_appkey()

        if await self._check_if_yagna_is_running():
            logger.info("Yagna service is already running")
        else:
            await self._run_yagna_service()

        # await self._run_yagna_payment_fund()

    async def shutdown(self):
        if self._yagna_process is None:
            return

        if self._yagna_process.returncode is None:
            self._yagna_process.terminate()

        await self._yagna_process.wait()

    async def _wait_for_yagna(self) -> bool:
        for _ in range(25):
            if await self._check_if_yagna_is_running():
                return True

            await asyncio.sleep(1)

        return False

    async def _check_if_yagna_is_running(self) -> bool:
        try:
            await run_subprocess(self._yagna_path, "id", "show")
        except GolemRayError:
            return False

        return True

    async def _run_yagna_payment_fund(self) -> bool:
        try:
            await run_subprocess(self._yagna_path, "payment", "fund")
        except GolemRayError:
            return False

        return True

    async def _run_yagna_service(self):
        process = await asyncio.create_subprocess_exec(self._yagna_path, "service", "run")

        is_running = await self._wait_for_yagna()

        if is_running:
            self._yagna_process = process
        else:
            logger.error("Failed to start yagna!")

    async def _get_or_create_yagna_appkey(self):
        if YAGNA_APPKEY:
            return YAGNA_APPKEY

        output = await run_subprocess(self._yagna_path, "app-key", "list", "--json")

        yagna_app = next((app for app in json.loads(output) if app["name"] == YAGNA_APPNAME), None)

        if yagna_app is not None:
            return yagna_app["key"]

        output = await run_subprocess(
            self._yagna_path,
            "app-key",
            "create",
            YAGNA_APPNAME,
            "--json",
        )

        return json.loads(output)
