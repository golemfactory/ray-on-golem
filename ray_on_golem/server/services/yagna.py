import asyncio
import json
import logging
import os
from asyncio.subprocess import Process
from pathlib import Path
from typing import Optional

import aiohttp

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.settings import YAGNA_API_URL, YAGNA_APPKEY, YAGNA_APPNAME
from ray_on_golem.utils import run_subprocess

logger = logging.getLogger(__name__)


class YagnaServiceError(RayOnGolemError):
    pass


class YagnaService:
    def __init__(self, yagna_path: Path):
        self._yagna_path = yagna_path

        self.yagna_appkey: Optional[str] = None
        self._yagna_process: Optional[Process] = None

    async def init(self) -> None:
        if await self._check_if_yagna_is_running():
            logger.info("Yagna service is already running")
        else:
            await self._run_yagna_service()
            await self._run_yagna_payment_init()

        self.yagna_appkey = await self._get_or_create_yagna_appkey()

    async def shutdown(self):
        await self._stop_yagna_service()

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

    async def _run_yagna_service(self) -> None:
        logger.info("Starting Yagna service...")

        # TODO: Add explicit logs when subprocess fails instantly (for e.g. when yagna_path
        #  is incorrect)
        process = await asyncio.create_subprocess_exec(
            self._yagna_path,
            "service",
            "run",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            preexec_fn=os.setpgrp,  # https://stackoverflow.com/a/5446982/1993670
        )

        is_running = await self._wait_for_yagna_api()

        if is_running:
            self._yagna_process = process
            logger.info("Starting Yagna service done")
        else:
            logger.error("Starting Yagna service failed!")

    async def _stop_yagna_service(self):
        if self._yagna_process is None:
            logger.info("No need to stop Yagna service, as it was started externally")
            return

        logger.info("Stopping Yagna service...")

        if self._yagna_process.returncode is None:
            self._yagna_process.terminate()

        await self._yagna_process.wait()

        logger.info("Stopping Yagna service done")

    async def _run_yagna_payment_init(self) -> None:
        await run_subprocess(self._yagna_path, "payment", "init")

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
