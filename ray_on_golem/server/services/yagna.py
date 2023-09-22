import asyncio
import json
import logging
from asyncio.subprocess import Process
from pathlib import Path
from typing import Optional

import aiohttp

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.settings import YAGNA_API_URL, YAGNA_APPKEY, YAGNA_APPNAME
from ray_on_golem.utils import run_subprocess, run_subprocess_output

logger = logging.getLogger(__name__)


class YagnaServiceError(RayOnGolemError):
    pass


class YagnaService:
    def __init__(self, yagna_path: Path):
        self._yagna_path = yagna_path

        self.yagna_appkey: Optional[str] = None
        self._yagna_process: Optional[Process] = None
        self._yagna_early_exit_task: Optional[asyncio.Task] = None

    async def init(self) -> None:
        logger.info("Starting YagnaService...")

        if await self._check_if_yagna_is_running():
            logger.info("No need to start Yagna, as it was started externally")
        else:
            await self._run_yagna()
            await self._run_yagna_payment_fund()

        self.yagna_appkey = await self._get_or_create_yagna_appkey()

        logger.info("Starting YagnaService done")

    async def shutdown(self) -> None:
        logger.info("Stopping YagnaService...")

        await self._stop_yagna_service()

        logger.info("Stopping YagnaService done")

    async def _wait_for_yagna_api(self) -> bool:
        for _ in range(25):
            if await self._check_if_yagna_is_running():
                return True

            await asyncio.sleep(1)

        return False

    async def _check_if_yagna_is_running(self) -> bool:
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(YAGNA_API_URL):
                    return True
        except aiohttp.ClientError:
            return False

    async def _run_yagna(self) -> None:
        logger.info("Starting Yagna...")

        # TODO: Add explicit logs when subprocess fails instantly (for e.g. when yagna_path
        #  is incorrect)
        self._yagna_process = await run_subprocess(self._yagna_path, "service", "run")
        self._yagna_early_exit_task = asyncio.create_task(self._on_yagna_early_exit())

        is_running = await self._wait_for_yagna_api()

        if is_running:
            logger.info("Starting Yagna done")
        else:
            logger.error("Starting Yagna failed!")

    async def _on_yagna_early_exit(self) -> None:
        await self._yagna_process.communicate()

        logger.warning(f"Yagna exited prematurely!")

    async def _stop_yagna_service(self) -> None:
        if self._yagna_process is None:
            logger.info("No need to stop Yagna, as it was started externally")
            return

        if self._yagna_process.returncode is not None:
            logger.info("No need to stop Yagna, as it's not running")
            return

        logger.info("Stopping Yagna...")

        self._yagna_early_exit_task.cancel()
        try:
            await self._yagna_early_exit_task
        except asyncio.CancelledError:
            pass

        self._yagna_process.terminate()
        await self._yagna_process.wait()

        logger.info("Stopping Yagna done")

    async def _run_yagna_payment_fund(self) -> None:
        await run_subprocess_output(self._yagna_path, "payment", "fund")

    async def _get_or_create_yagna_appkey(self) -> str:
        if YAGNA_APPKEY:
            return YAGNA_APPKEY

        output = await run_subprocess_output(self._yagna_path, "app-key", "list", "--json")

        yagna_app = next((app for app in json.loads(output) if app["name"] == YAGNA_APPNAME), None)

        if yagna_app is not None:
            return yagna_app["key"]

        output = await run_subprocess_output(
            self._yagna_path,
            "app-key",
            "create",
            YAGNA_APPNAME,
            "--json",
        )

        return json.loads(output)
