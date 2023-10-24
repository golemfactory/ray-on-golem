import asyncio
import json
import logging
from asyncio.subprocess import Process
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.settings import (
    LOGGING_YAGNA_PATH,
    RAY_ON_GOLEM_CHECK_DEADLINE,
    YAGNA_API_URL,
    YAGNA_APPKEY,
    YAGNA_APPNAME,
    YAGNA_CHECK_DEADLINE,
    YAGNA_START_DEADLINE,
)
from ray_on_golem.utils import get_last_lines_from_file, run_subprocess, run_subprocess_output

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
            logger.info("Not starting Yagna, as it was started externally")
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
        logger.debug("Waiting for Yagna Api...")

        check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())
        for _ in range(25):
            if await self._check_if_yagna_is_running():
                logger.debug("Waiting for Yagna Api done")
                return True

            logger.debug(
                "Yagna Api not yet ready, waiting additional `%s` seconds...", check_seconds
            )
            await asyncio.sleep(check_seconds)

        logger.debug("Waiting for Yagna Api failed with timeout!")

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

        log_file = LOGGING_YAGNA_PATH.open("w")
        self._yagna_process = await run_subprocess(
            self._yagna_path, "service", "run", stderr=log_file, stdout=log_file
        )

        start_deadline = datetime.now() + YAGNA_START_DEADLINE
        check_seconds = int(YAGNA_CHECK_DEADLINE.total_seconds())
        while datetime.now() < start_deadline:
            try:
                await asyncio.wait_for(self._yagna_process.communicate(), timeout=check_seconds)
            except asyncio.TimeoutError:
                if await self._check_if_yagna_is_running():
                    self._yagna_early_exit_task = asyncio.create_task(self._on_yagna_early_exit())
                    logger.info("Starting Yagna done")
                    return
            else:
                logger.error(
                    "Starting Yagna failed!\nShowing last 50 lines from `%s`:\n%s",
                    LOGGING_YAGNA_PATH,
                    get_last_lines_from_file(LOGGING_YAGNA_PATH, 50),
                )
                raise YagnaServiceError("Starting Yagna failed!")

            logger.info(
                "Yagna is not yet running, waiting additional `%s` seconds...",
                check_seconds,
            )

        logger.error(
            "Starting Yagna failed! Deadline of `%s` reached.\nShowing last 50 lines from `%s`:\n%s",
            YAGNA_START_DEADLINE,
            LOGGING_YAGNA_PATH,
            get_last_lines_from_file(LOGGING_YAGNA_PATH, 50),
        )
        raise YagnaServiceError("Starting Yagna failed!")

    async def _on_yagna_early_exit(self) -> None:
        await self._yagna_process.communicate()

        logger.warning(f"Yagna exited prematurely!")

    async def _stop_yagna_service(self) -> None:
        if self._yagna_process is None:
            logger.info("Not stopping Yagna, as it was started externally")
            return

        if self._yagna_process.returncode is not None:
            logger.info("Not stopping Yagna, as it's not running")
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
