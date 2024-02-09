import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ray_on_golem.log import ZippingRotatingFileHandler
from ray_on_golem.server.models import ShutdownState
from ray_on_golem.server.settings import (
    LOGGING_BACKUP_COUNT,
    RAY_ON_GOLEM_CHECK_DEADLINE,
    RAY_ON_GOLEM_PATH,
    RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
    RAY_ON_GOLEM_START_DEADLINE,
    get_log_path,
)
from ray_on_golem.utils import get_last_lines_from_file

if TYPE_CHECKING:
    from ray_on_golem.client import RayOnGolemClient
    from ray_on_golem.ctl.log import RayOnGolemCtlLogger


class RayOnGolemCtl:
    def __init__(self, client: "RayOnGolemClient", output_logger: "RayOnGolemCtlLogger"):
        self._client = client
        self._output_logger = output_logger

    def start_webserver(
        self,
        registry_stats: bool,
        datadir: Optional[Path] = None,
        self_shutdown: bool = True,
    ) -> None:
        webserver_status = self._client.get_webserver_status()
        if webserver_status:
            if webserver_status.shutting_down:
                self.wait_for_shutdown()
            else:
                self._output_logger.info("Not starting webserver, as it's already running")
                if datadir and webserver_status.datadir != str(datadir):
                    self._output_logger.warning(
                        f"Specified data directory `{datadir}` "
                        f"is different than webserver's: `{webserver_status.datadir}`. "
                        "Using the webserver setting."
                    )
                return

        self._output_logger.info(
            f"Starting webserver with deadline up to `{RAY_ON_GOLEM_START_DEADLINE}`..."
        )
        args = [
            RAY_ON_GOLEM_PATH,
            "webserver",
            "-p",
            str(self._client.port),
            "--registry-stats" if registry_stats else "--no-registry-stats",
            "--self-shutdown" if self_shutdown else "--no-self-shutdown",
        ]

        if datadir:
            args.extend(["--datadir", datadir])

        self._output_logger.verbose(f"Webserver command: `{' '.join([str(a) for a in args])}`")

        log_file_path = get_log_path("webserver_debug", datadir)
        debug_logger = ZippingRotatingFileHandler(log_file_path, backupCount=LOGGING_BACKUP_COUNT)
        proc = subprocess.Popen(
            args,
            stdout=debug_logger.stream,
            stderr=debug_logger.stream,
            start_new_session=True,
        )

        start_deadline = datetime.now() + RAY_ON_GOLEM_START_DEADLINE
        check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())
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
            f"Starting webserver failed! Deadline of `{RAY_ON_GOLEM_START_DEADLINE}` reached.\n"
            "Showing last 50 lines from "
            f"`{log_file_path}`:\n{get_last_lines_from_file(log_file_path, 50)}"
        )

    def stop_webserver(self,
        ignore_self_shutdown: bool = False,
        force_shutdown: bool = False
   ) -> None:
        webserver_serviceable = self._client.is_webserver_serviceable()
        if not webserver_serviceable:
            if webserver_serviceable is None:
                self._output_logger.info("Not stopping the webserver, as it's not running")
            else:
                self._output_logger.info(
                    "Not stopping the webserver, as it's already shutting down"
                )

            return

        self._output_logger.info("Requesting webserver shutdown...")

        shutdown_state = self._client.shutdown_webserver()

        if shutdown_state == ShutdownState.NOT_ENABLED:
            self._output_logger.info("Not stopping webserver, as it was started externally")
            return
        elif shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
            self._output_logger.info("Not stopping webserver, as the cluster is not empty")
            return

        self._output_logger.info("Requesting webserver shutdown done, will stop soon")

    def wait_for_shutdown(self) -> None:
        self._output_logger.info(
            "Previous webserver instance is still shutting down, "
            f"waiting with deadline up to `{RAY_ON_GOLEM_SHUTDOWN_DEADLINE}`...",
        )

        wait_deadline = datetime.now() + RAY_ON_GOLEM_SHUTDOWN_DEADLINE
        check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())

        time.sleep(check_seconds)
        while datetime.now() < wait_deadline:
            webserver_serviceable = self._client.is_webserver_serviceable()
            if webserver_serviceable is None:
                self._output_logger.info("Previous webserver instance shutdown done")
                return

            self._output_logger.info(
                "Previous webserver instance is not yet shutdown, "
                f"waiting additional `{check_seconds}` seconds..."
            )
            time.sleep(check_seconds)

        self._output_logger.error(
            "Previous webserver instance is still running! "
            f"Deadline of `{RAY_ON_GOLEM_START_DEADLINE}` reached."
        )
