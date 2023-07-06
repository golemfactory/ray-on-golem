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
    timeout = 5  # in seconds

    def __init__(self):
        self._is_running = self._run()
        self._yagna_process: subprocess.Popen | None = None

    @staticmethod
    def listen_output(process, look_for_string: str):
        for line in process.stdout:
            line = line.decode('utf-8').strip()  # Convert bytes to string
            if look_for_string in line:
                break  # Stop listening when the desired message is found

    def _check_if_yagna_is_running(self):
        result = subprocess.run(['yagna', 'net', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            stdout_output = result.stdout
            if self.yagna_running_string in stdout_output:
                return True
            else:
                return False
        else:
            raise GolemRayException(message='Cant check yagna status', status_code=StatusCode.SERVER_ERROR)

    def run_yagna_payment_fund(self):
        result = subprocess.run(self.payment_fund_command, capture_output=True, text=True)
        if result.returncode == 0:
            stdout_output = result.stdout
            if self.payment_fund_success_string in stdout_output:
                return True
            else:
                raise GolemRayException(message='Cant fund payment in yagna', status_code=StatusCode.SERVER_ERROR)
        else:
            raise GolemRayException(message='Cant check yagna status', status_code=StatusCode.SERVER_ERROR)

    def _run_yagna_service(self):
        process = subprocess.Popen(self.run_command, stdout=subprocess.PIPE)
        self.listen_output(process, self.yagna_started_string)
        self._yagna_process = process

    def _run(self) -> bool:
        if self._check_if_yagna_is_running():
            logger.info('Yagna service is running')
        else:
            self._run_yagna_service()

        if self.run_yagna_payment_fund():
            pass
        else:
            raise

    def shutdown(self):
        if self._yagna_process:
            self._yagna_process.terminate()
