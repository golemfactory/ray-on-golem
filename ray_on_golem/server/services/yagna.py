import asyncio
import json
import logging
from asyncio.subprocess import Process
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import aiohttp

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.log import ZippingRotatingFileHandler
from ray_on_golem.server.settings import (
    LOGGING_BACKUP_COUNT,
    PAYMENT_NETWORK_MAINNET,
    PAYMENT_NETWORK_POLYGON,
    RAY_ON_GOLEM_CHECK_INTERVAL,
    YAGNA_API_URL,
    YAGNA_APPKEY,
    YAGNA_APPNAME,
    YAGNA_CHECK_INTERVAL,
    YAGNA_FUND_TIMEOUT,
    YAGNA_START_TIMEOUT,
    get_log_path,
)
from ray_on_golem.utils import get_last_lines_from_file, run_subprocess, run_subprocess_output

logger = logging.getLogger(__name__)


class YagnaServiceError(RayOnGolemError):
    pass


class YagnaService:
    def __init__(self, yagna_path: Path, datadir: Path):
        self._yagna_path = yagna_path

        self.yagna_appkey: Optional[str] = None
        self._yagna_process: Optional[Process] = None
        self._yagna_early_exit_task: Optional[asyncio.Task] = None
        self._datadir = datadir

    async def start(self) -> None:
        logger.info("Starting YagnaService...")

        if await self._check_if_yagna_is_running():
            logger.info("Not starting Yagna, as it was started externally")
        else:
            await self._run_yagna()

        self.yagna_appkey = await self._get_or_create_yagna_appkey()

        logger.info("Starting YagnaService done")

    async def stop(self) -> None:
        logger.info("Stopping YagnaService...")

        await self._stop_yagna_service()

        logger.info("Stopping YagnaService done")

    async def _wait_for_yagna_api(self) -> bool:
        logger.debug("Waiting for Yagna Api...")

        check_seconds = int(RAY_ON_GOLEM_CHECK_INTERVAL.total_seconds())
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
        logger.debug("Checking yagna instance at %s...", YAGNA_API_URL)

        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(YAGNA_API_URL):
                    logger.debug("Checking yagna instance at %s done", YAGNA_API_URL)
                    return True
        except aiohttp.ClientError:
            logger.debug("Checking yagna instance at %s failed", YAGNA_API_URL)
            return False

    async def _run_yagna(self) -> None:
        logger.info("Starting Yagna...")

        log_file_path = get_log_path("yagna", self._datadir)
        yagna_logger = ZippingRotatingFileHandler(log_file_path, backupCount=LOGGING_BACKUP_COUNT)

        self._yagna_process = await run_subprocess(
            self._yagna_path,
            "service",
            "run",
            stderr=yagna_logger.stream,
            stdout=yagna_logger.stream,
            detach=True,
        )

        start_deadline = datetime.now() + YAGNA_START_TIMEOUT
        check_seconds = int(YAGNA_CHECK_INTERVAL.total_seconds())
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
                    log_file_path,
                    get_last_lines_from_file(log_file_path, 50),
                )
                raise YagnaServiceError("Starting Yagna failed!")

            logger.info(
                "Yagna is not yet running, waiting additional `%s` seconds...",
                check_seconds,
            )

        logger.error(
            "Starting Yagna failed! Timeout of `%s` reached.\nShowing last 50 lines from `%s`:\n%s",
            YAGNA_START_TIMEOUT,
            log_file_path,
            get_last_lines_from_file(log_file_path, 50),
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

    async def prepare_funds(self, network: str, driver: str) -> Dict:
        platform = f"{driver}/{network}"

        # FIXME: Uncomment this block on yagna 0.15+
        # if network not in (PAYMENT_NETWORK_HOLESKY, PAYMENT_NETWORK_GOERLI):
        #     logger.debug(
        #         "No need to prepare funds as `%s` does not support automatic funding",
        #         platform,
        #     )
        #
        #     return json.loads(
        #         await run_subprocess_output(
        #             self._yagna_path,
        #             "payment",
        #             "status",
        #             "--network",
        #             network,
        #             "--driver",
        #             driver,
        #             "--json",
        #             timeout=timedelta(seconds=30),
        #         )
        #     )

        logger.debug(
            "Preparing `%s` funds with a timeout up to %s...",
            platform,
            YAGNA_FUND_TIMEOUT,
        )

        # FIXME: is_mainnet not needed on yagna 0.15+
        is_mainnet = network in (PAYMENT_NETWORK_MAINNET, PAYMENT_NETWORK_POLYGON)
        fund_deadline = datetime.now() + YAGNA_FUND_TIMEOUT
        check_seconds = int(YAGNA_CHECK_INTERVAL.total_seconds())
        while datetime.now() < fund_deadline:
            try:
                await run_subprocess_output(
                    self._yagna_path,
                    "payment",
                    *(["init", "--sender"] if is_mainnet else ["fund"]),
                    "--network",
                    network,
                    "--driver",
                    driver,
                )
            except RayOnGolemError as e:
                logger.error("Preparing `%s` funds failed with error: %s", platform, e)
            else:
                output = json.loads(
                    await run_subprocess_output(
                        self._yagna_path,
                        "payment",
                        "status",
                        "--network",
                        network,
                        "--driver",
                        driver,
                        "--json",
                        timeout=timedelta(seconds=30),
                    )
                )

                amount = float(output["amount"])

                if amount or is_mainnet:
                    logger.debug(
                        "Preparing `%s` funds done with balance of %.2f %s",
                        platform,
                        amount,
                        output["token"],
                    )
                    return output
                else:
                    logger.debug(
                        "Prepared funds seems not yet available, waiting additional `%s` seconds...",
                        check_seconds,
                    )

            await asyncio.sleep(check_seconds)

        raise YagnaServiceError(
            f"Can't prepare `{platform}` funds! Timeout of `{YAGNA_FUND_TIMEOUT}` reached."
        )

    async def fetch_payment_status(self, network: str, driver: str) -> str:
        output = await run_subprocess_output(
            self._yagna_path,
            "payment",
            "status",
            "--network",
            network,
            "--driver",
            driver,
            timeout=timedelta(seconds=30),
        )
        return output.decode()

    async def fetch_wallet_address(self) -> str:
        id_list = json.loads(await run_subprocess_output(self._yagna_path, "id", "list", "--json"))

        for identity in id_list:
            if identity["default"]:
                return identity["address"]

        raise YagnaServiceError(f"Default wallet not found for app_key `{self.yagna_appkey}`!")

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
