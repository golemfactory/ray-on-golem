import asyncio
import subprocess

from app.consts import StatusCode
from app.logger import get_logger
from app.middlewares.error_handling import GolemRayException

logger = get_logger()


class YagnaManager:
    run_command = ['yagna', 'service', 'run']
    payment_fund_command = ['yagna', 'payment', 'fund']
    yagna_running_string = 'Error: yagna is already running'
    payment_fund_success_string = 'Received funds from the faucet'
    yagna_started_string = 'Http server thread started on'
    timeout = 20  # in seconds

    def __init__(self):
        self._is_running = False
        self._yagna_process: subprocess.Popen | None = None

    async def run(self) -> None:
        if await self._check_if_yagna_is_running():
            logger.info('Yagna service is running')
        else:
            await self._run_yagna_service()

        await self._run_yagna_payment_fund()

    def shutdown(self):
        if self._yagna_process:
            self._yagna_process.terminate()

    async def _listen_output(self, process):
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.decode('utf-8').strip()  # Convert bytes to string
            if self.yagna_running_string in line:
                return True  # Stop listening when the desired message is found
            if self.yagna_started_string in line:
                return True

    async def _check_if_yagna_is_running(self):
        result = await asyncio.create_subprocess_exec('yagna', 'net', 'status',
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        stdout_output, _ = await result.communicate()
        stdout_output = stdout_output.decode('utf-8')
        if self.yagna_running_string in stdout_output:
            return True
        else:
            return False

    async def _run_yagna_payment_fund(self):
        result = await asyncio.create_subprocess_exec(*self.payment_fund_command,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE)
        stdout_output, _ = await result.communicate()
        if result.returncode == 0:
            stdout_output = stdout_output.decode('utf-8')
            if self.payment_fund_success_string in stdout_output:
                return True
            else:
                raise GolemRayException(message='Cant fund payment in yagna',
                                        status_code=StatusCode.SERVER_ERROR)
        else:
            raise GolemRayException(message='Cant check yagna status',
                                    status_code=StatusCode.SERVER_ERROR)

    async def _run_yagna_service(self):
        try:
            process = await asyncio.create_subprocess_exec(*self.run_command, stdout=subprocess.PIPE)
            running = await asyncio.wait_for(self._listen_output(process), timeout=self.timeout)
            if running:
                self._yagna_process = process
                self._is_running = True

        except asyncio.TimeoutError:
            logger.error("Can't run yagna service.")
