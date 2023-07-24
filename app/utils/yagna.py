import asyncio
import subprocess
from asyncio.subprocess import Process

from app.consts import StatusCode
from app.logger import get_logger
from app.middlewares.error_handling import GolemRayException

logger = get_logger()


class YagnaManager:
    run_command = ['yagna', 'service', 'run']
    payment_fund_command = ['yagna', 'payment', 'fund']
    yagna_running_string = 'yagna is already running'
    payment_fund_success_string = 'Received funds from the faucet'
    yagna_started_string = 'Server listening on'
    timeout = 60  # in seconds

    def __init__(self):
        self._is_running = False
        self._yagna_process: Process | None = None

    async def __aenter__(self) -> 'YagnaManager':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

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
            try:
                # self._yagna_process.terminate()
                await self._yagna_process.wait()
            except asyncio.CancelledError:
                await self._yagna_process.wait()
                # self._yagna_process.kill()

    ##
    # Private
    async def _wait_for_yagna(self):
        while True:
            await asyncio.sleep(25)
            if await self._check_if_yagna_is_running():
                break

        return True

    async def _check_if_yagna_is_running(self):
        process = await asyncio.create_subprocess_exec('yagna', 'net', 'status',
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
            # stdout_output = stdout_output.decode('utf-8')
            # if self.payment_fund_success_string in stdout_output:
            #     return True
            # else:
            #     raise GolemRayException(message='Cant fund payment in yagna',
            #                             status_code=StatusCode.SERVER_ERROR)
        else:
            raise GolemRayException(message='Cant check yagna status',
                                    status_code=StatusCode.SERVER_ERROR)

    async def _run_yagna_service(self):
        try:
            process = await asyncio.create_subprocess_shell(cmd='yagna service run', stdout=subprocess.PIPE)
            running = await self._wait_for_yagna()
            if running:
                self._yagna_process = process
                self._is_running = True

        except asyncio.TimeoutError:
            logger.error("Can't run yagna service.")
