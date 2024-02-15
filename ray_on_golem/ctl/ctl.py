import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import psutil

from ray_on_golem.log import ZippingRotatingFileHandler
from ray_on_golem.server.models import ShutdownState
from ray_on_golem.server.settings import (
    LOGGING_BACKUP_COUNT,
    RAY_ON_GOLEM_CHECK_INTERVAL,
    RAY_ON_GOLEM_PATH,
    RAY_ON_GOLEM_PID_FILENAME,
    RAY_ON_GOLEM_SHUTDOWN_DELAY,
    RAY_ON_GOLEM_SHUTDOWN_TIMEOUT,
    RAY_ON_GOLEM_START_TIMEOUT,
    RAY_ON_GOLEM_STOP_TIMEOUT,
    get_datadir,
    get_log_path,
)
from ray_on_golem.utils import get_last_lines_from_file

if TYPE_CHECKING:
    from ray_on_golem.client import RayOnGolemClient
    from ray_on_golem.ctl.log import RayOnGolemCtlLogger


class RayOnGolemCtl:
    def __init__(
        self,
        client: "RayOnGolemClient",
        output_logger: "RayOnGolemCtlLogger",
        datadir: Optional[Path] = None,
    ):
        self._client = client
        self._output_logger = output_logger
        self._datadir = datadir

    def start_webserver(
        self,
        registry_stats: bool,
        self_shutdown: bool = True,
    ) -> None:
        webserver_status = self._client.get_webserver_status()
        if webserver_status:
            if webserver_status.shutting_down:
                self.wait_for_stop()
            else:
                self._output_logger.info("Not starting the webserver, as it's already running")
                if self._datadir and webserver_status.datadir != str(self._datadir):
                    self._output_logger.warning(
                        f"Specified data directory `{self._datadir}` "
                        f"is different than webserver's: `{webserver_status.datadir}`. "
                        "Using the webserver setting."
                    )
                return

        self._output_logger.info(f"Starting webserver on {self._client.base_url}...")
        self._output_logger.verbose(f"Webserver startup timeout: `{RAY_ON_GOLEM_START_TIMEOUT}`.")
        args = [
            RAY_ON_GOLEM_PATH,
            "webserver",
            "-p",
            str(self._client.port),
            "--registry-stats" if registry_stats else "--no-registry-stats",
            "--self-shutdown" if self_shutdown else "--no-self-shutdown",
        ]

        if self._datadir:
            args.extend(["--datadir", self._datadir])

        self._output_logger.verbose(f"Webserver command: `{' '.join([str(a) for a in args])}`")

        log_file_path = get_log_path("webserver_debug", self._datadir)
        debug_logger = ZippingRotatingFileHandler(log_file_path, backupCount=LOGGING_BACKUP_COUNT)
        proc = subprocess.Popen(
            args,
            stdout=debug_logger.stream,
            stderr=debug_logger.stream,
            start_new_session=True,
        )
        self._save_pid(proc.pid)

        start_deadline = datetime.now() + RAY_ON_GOLEM_START_TIMEOUT
        check_seconds = int(RAY_ON_GOLEM_CHECK_INTERVAL.total_seconds())
        while datetime.now() < start_deadline:
            try:
                proc.communicate(timeout=check_seconds)
            except subprocess.TimeoutExpired:
                if self._client.is_webserver_serviceable():
                    self._output_logger.info("Starting webserver done")
                    return
            else:
                self._output_logger.error(
                    "Starting webserver failed!\n"
                    f"Showing last 50 lines from `{log_file_path}`:\n"
                    f"{get_last_lines_from_file(log_file_path, 50)}"
                )

            self._output_logger.info(
                f"Webserver is not yet running, waiting additional `{check_seconds}` seconds..."
            )

        self._output_logger.error(
            f"Starting webserver failed! Timeout of `{RAY_ON_GOLEM_START_TIMEOUT}` reached.\n"
            "Showing last 50 lines from "
            f"`{log_file_path}`:\n{get_last_lines_from_file(log_file_path, 50)}"
        )

    def stop_webserver(
        self,
        ignore_self_shutdown: bool = False,
        force_shutdown: bool = False,
        shutdown_delay: timedelta = RAY_ON_GOLEM_SHUTDOWN_DELAY,
    ) -> Optional[ShutdownState]:
        webserver_serviceable = self._client.is_webserver_serviceable()
        if not webserver_serviceable:
            if webserver_serviceable is None:
                self._output_logger.info(f"No webserver found on: {self._client.base_url}.")
            else:
                self._output_logger.info("The webserver is already shutting down.")

            return

        self._output_logger.info(
            "{verb} webserver shutdown...".format(
                verb="Requesting" if not force_shutdown else "Forcing"
            )
        )

        shutdown_state = self._client.shutdown_webserver(
            ignore_self_shutdown=ignore_self_shutdown,
            force_shutdown=force_shutdown,
            shutdown_delay=shutdown_delay,
        )

        if shutdown_state == ShutdownState.NOT_ENABLED:
            self._output_logger.info("Cannot stop the webserver, as it was started externally.")
        elif shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
            self._output_logger.info("Cannot stop the webserver, as the cluster is not empty.")
        elif shutdown_state == ShutdownState.FORCED_SHUTDOWN:
            self._output_logger.info("Force-shutdown requested, will stop soon.")
        else:
            self._output_logger.info("Webserver shutdown requested, will stop soon.")

        return shutdown_state

    def wait_for_stop(
        self,
        starting_up=True,
        shutdown_timeout: timedelta = RAY_ON_GOLEM_SHUTDOWN_TIMEOUT,
        stop_timeout: timedelta = RAY_ON_GOLEM_STOP_TIMEOUT,
    ):
        self._wait_for_shutdown(starting_up=starting_up, timeout=shutdown_timeout)
        self._wait_for_process_stop(starting_up=starting_up, timeout=stop_timeout)

    def _wait_for_shutdown(self, starting_up: bool, timeout: timedelta) -> None:
        webserver = "Previous webserver instance" if starting_up else "Webserver"
        if self._client.is_webserver_serviceable() is None:
            return

        self._output_logger.info(
            f"{webserver} is still shutting down, "
            f"waiting up to {int(timeout.total_seconds())} seconds ...",
        )

        wait_deadline = datetime.now() + timeout
        check_seconds = int(RAY_ON_GOLEM_CHECK_INTERVAL.total_seconds())

        while datetime.now() < wait_deadline:
            time.sleep(check_seconds)
            webserver_serviceable = self._client.is_webserver_serviceable()
            if webserver_serviceable is None:
                self._output_logger.info(f"{webserver} shutdown completed.")
                return

            self._output_logger.verbose(
                f"{webserver} is still running, waiting additional `{check_seconds}` seconds..."
            )

        self._output_logger.error(f"Shutdown timeout of {timeout} reached.")

    def _wait_for_process_stop(self, starting_up: bool, timeout: timedelta):
        wait_deadline = datetime.now() + timeout
        check_seconds = int(RAY_ON_GOLEM_CHECK_INTERVAL.total_seconds())
        cnt = 0
        webserver = "previous webserver process" if starting_up else "webserver process"

        while datetime.now() < wait_deadline:
            proc = self.get_process_info()

            if not proc:
                if cnt:
                    # only mention stopping if any process had been running
                    self._output_logger.info(f"{webserver.capitalize()} stopped.")
                    self.clear_pid()
                return

            if not cnt:
                self._output_logger.info(
                    f"Waiting {int(timeout.total_seconds())} seconds for the {webserver} to stop."
                )
            else:
                self._output_logger.verbose(f"Waiting additional `{check_seconds}`...")

            cnt += 1
            time.sleep(check_seconds)

        self._output_logger.error(f"{webserver.capitalize()} stop timeout of {timeout} reached.")

    def _get_pidfile(self) -> Path:
        return get_datadir(self._datadir) / RAY_ON_GOLEM_PID_FILENAME

    def _save_pid(self, pid: int):
        with self._get_pidfile().open("w") as pidf:
            pidf.write(str(pid))

    def clear_pid(self):
        try:
            self._get_pidfile().unlink()
        except FileNotFoundError:
            pass

    def get_process_info(self) -> Optional[psutil.Process]:
        try:
            pidfile_path = self._get_pidfile()
            with pidfile_path.open("r") as pidf:
                process = psutil.Process(int(pidf.read()))
                if pidfile_path.stat().st_mtime >= process.create_time():
                    return process
        except (FileNotFoundError, ValueError, psutil.NoSuchProcess):
            return None
