import asyncio
import json
import logging
import subprocess
from asyncio.subprocess import Process
from subprocess import check_output
from typing import Optional

from golem_ray.server.config import YAGNA_APPKEY
from golem_ray.server.exceptions import CheckYagnaStatusError

logger = logging.getLogger('yagna-service')


class YagnaManager:
    YAGNA_APPNAME = 'golem-ray'

    def __init__(self, yagna_path: str):
        self.yagna_path: str = yagna_path
        self.yagna_appkey: str = self.get_or_create_yagna_appkey()
        self.run_command = [yagna_path, 'service', 'run']
        self.net_status_command = [yagna_path, 'net', 'status']
        self.payment_fund_command = [yagna_path, 'payment', 'fund']
        self._is_running = False
        self._yagna_process: Optional[Process] = None

    ##
    # Public
    async def run(self) -> None:
        if await self._check_if_yagna_is_running():
            logger.info('Yagna service is running')
        else:
            await self._run_yagna_service()

        await self._run_yagna_payment_fund()

    async def shutdown(self):
        if self._yagna_process:
            if self._yagna_process.returncode is None:
                self._yagna_process.terminate()
            await self._yagna_process.wait()

    ##
    # Private
    async def _wait_for_yagna(self):
        while True:
            await asyncio.sleep(25)
            if await self._check_if_yagna_is_running():
                break

        return True

    async def _check_if_yagna_is_running(self):
        process = await asyncio.create_subprocess_exec(*self.net_status_command,
                                                       stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE)
        stdout_output, _ = await process.communicate()
        if process.returncode == 0:
            return True
        else:
            return False

    async def _run_yagna_payment_fund(self):
        result = await asyncio.create_subprocess_exec(*self.payment_fund_command,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        stdout_output, _ = await result.communicate()
        if result.returncode == 0:
            await asyncio.sleep(2)
            return True
        else:
            raise CheckYagnaStatusError

    async def _run_yagna_service(self):
        try:
            process = await asyncio.create_subprocess_exec(*self.run_command,
                                                           stdout=subprocess.PIPE)
            running = await self._wait_for_yagna()
            if running:
                self._yagna_process = process
                self._is_running = True

        except asyncio.TimeoutError:
            logger.error("Can't run yagna service.")

    def get_or_create_yagna_appkey(self):
        if YAGNA_APPKEY:
            return YAGNA_APPKEY
        id_data = json.loads(check_output(["yagna", "server-key", "list", "--json"]))
        yagna_app = next((app for app in id_data if app['name'] == self.YAGNA_APPNAME), None)
        if yagna_app is None:
            return check_output(["yagna", "server-key", "create", self.YAGNA_APPNAME]).decode('utf-8').strip('"\n')
        else:
            return yagna_app['key']
