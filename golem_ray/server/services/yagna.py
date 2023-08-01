import asyncio
import json
import os
import subprocess
from asyncio.subprocess import Process
from subprocess import check_output

import dotenv

from golem_ray.server.consts import StatusCode
from golem_ray.server.logger import get_logger
from golem_ray.server.middlewares.error_handling import GolemRayException

dotenv.load_dotenv()
logger = get_logger()

YAGNA_APPNAME = 'requestor-mainnet'


class YagnaManager:
    yagna_path = os.getenv('YAGNA_PATH') or 'yagna'
    run_command = [f'{yagna_path}', 'service', 'run']
    payment_fund_command = [f'{yagna_path}', 'payment', 'fund']
    yagna_running_string = 'yagna is already running'
    payment_fund_success_string = 'Received funds from the faucet'
    yagna_started_string = 'Server listening on'
    timeout = 60  # in seconds

    def __init__(self):
        self._is_running = False
        self._yagna_process: Process | None = None

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
        process = await asyncio.create_subprocess_exec(f'{self.yagna_path}', 'net', 'status',
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
            raise GolemRayException(message='Cant check yagna status',
                                    status_code=StatusCode.SERVER_ERROR)

    async def _run_yagna_service(self):
        try:
            process = await asyncio.create_subprocess_shell(cmd=f'{self.yagna_path} service run',
                                                            stdout=subprocess.PIPE)
            running = await self._wait_for_yagna()
            if running:
                self._yagna_process = process
                self._is_running = True

        except asyncio.TimeoutError:
            logger.error("Can't run yagna service.")


def get_or_create_yagna_appkey():
    if os.getenv('YAGNA_APPKEY'):
        return os.getenv('YAGNA_APPKEY')
    id_data = json.loads(check_output(["yagna", "server-key", "list", "--json"]))
    yagna_app = next((app for app in id_data if app['name'] == YAGNA_APPNAME), None)
    if yagna_app is None:
        return check_output(["yagna", "server-key", "create", YAGNA_APPNAME]).decode('utf-8').strip('"\n')
    else:
        return yagna_app['key']
