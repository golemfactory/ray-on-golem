from datetime import datetime
from functools import lru_cache
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import requests
from pydantic import BaseModel, ValidationError
from ray.autoscaler._private.cli_logger import cli_logger  # noqa
from yarl import URL

from ray_on_golem.client.exceptions import RayOnGolemClientError, RayOnGolemClientValidationError
from ray_on_golem.log import ZippingRotatingFileHandler
from ray_on_golem.server import models, settings
from ray_on_golem.server.models import CreateClusterResponseData, ShutdownState
from ray_on_golem.server.settings import (
    LOG_GROUP,
    LOGGING_BACKUP_COUNT,
    RAY_ON_GOLEM_CHECK_DEADLINE,
    RAY_ON_GOLEM_PATH,
    RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
    RAY_ON_GOLEM_START_DEADLINE,
    get_log_path,

)
from ray_on_golem.utils import (
    is_running_on_golem_network,
    get_last_lines_from_file,
)

TResponseModel = TypeVar("TResponseModel")


class RayOnGolemClient:
    def __init__(self, port: int) -> None:
        self._base_url = URL("http://127.0.0.1").with_port(port)

        self._session = requests.Session()

    @classmethod
    @lru_cache()
    def get_instance(
        cls,
        webserver_port: int,
        enable_registry_stats: bool = True,
        datadir: Optional[Union[str, Path]] = None,
        self_shutdown: bool = True,
        start_webserver: bool = True,
    ) -> "RayOnGolemClient":
        client = RayOnGolemClient(webserver_port)

        if datadir and not isinstance(datadir, Path):
            datadir = Path(datadir)

        # consider starting the webserver only if this code is executed
        # on a requestor agent and not inside the VM on a provider
        if not is_running_on_golem_network() and start_webserver:
            client.start_webserver(
                webserver_port,
                enable_registry_stats,
                datadir,
                self_shutdown,
            )

        return client

    def start_webserver(
        self,
        port: int,
        registry_stats: bool,
        datadir: Optional[Path] = None,
        self_shutdown: bool = True,
    ) -> None:
        with cli_logger.group(LOG_GROUP):
            webserver_status = self.get_webserver_status()
            if webserver_status:
                if webserver_status.shutting_down:
                    self.wait_for_shutdown()
                else:
                    cli_logger.print("Not starting webserver, as it's already running")
                    if datadir and webserver_status.datadir != datadir:
                        cli_logger.warning(
                            "Specified data directory `{}` is different than webserver's: `{}`. "
                            "Using the webserver setting.",
                            datadir,
                            webserver_status.datadir,
                        )
                    return

            cli_logger.print(
                "Starting webserver with deadline up to `{}`...", RAY_ON_GOLEM_START_DEADLINE
            )
            args = [
                RAY_ON_GOLEM_PATH,
                "webserver",
                "-p",
                str(port),
                "--registry-stats" if registry_stats else "--no-registry-stats",
                "--self-shutdown" if self_shutdown else "--no-self-shutdown",
            ]

            if datadir:
                args.extend(["--datadir", datadir])

            cli_logger.verbose("Webserver command: `{}`", " ".join([str(a) for a in args]))

            log_file_path = get_log_path("webserver_debug", datadir)
            debug_logger = ZippingRotatingFileHandler(
                log_file_path, backupCount=LOGGING_BACKUP_COUNT
            )
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
                    if self.is_webserver_serviceable():
                        cli_logger.print("Starting webserver done")
                        return
                else:
                    cli_logger.abort(
                        "Starting webserver failed!\nShowing last 50 lines from `{}`:\n{}",
                        log_file_path,
                        get_last_lines_from_file(log_file_path, 50),
                    )

                cli_logger.print(
                    "Webserver is not yet running, waiting additional `{}` seconds...",
                    check_seconds,
                )

            cli_logger.abort(
                "Starting webserver failed! Deadline of `{}` reached.\n"
                "Showing last 50 lines from `{}`:\n{}",
                RAY_ON_GOLEM_START_DEADLINE,
                log_file_path,
                get_last_lines_from_file(log_file_path, 50),
            )

    def stop_webserver(self) -> None:
        with cli_logger.group(LOG_GROUP):
            webserver_serviceable = self.is_webserver_serviceable()
            if not webserver_serviceable:
                if webserver_serviceable is None:
                    cli_logger.print("Not stopping the webserver, as it's not running")
                else:
                    cli_logger.print("Not stopping the webserver, as it's already shutting down")

                return

            cli_logger.print("Requesting webserver shutdown...")

            shutdown_state = self.shutdown_webserver()

            if shutdown_state == ShutdownState.NOT_ENABLED:
                cli_logger.print("Not stopping webserver, as it was started externally")
                return
            elif shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
                cli_logger.print("Not stopping webserver, as the cluster is not empty")
                return

            cli_logger.print("Requesting webserver shutdown done, will stop soon")

    def wait_for_shutdown(self) -> None:
        cli_logger.print(
            "Previous webserver instance is still shutting down, "
            "waiting with deadline up to `{}`...",
            RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
        )

        wait_deadline = datetime.now() + RAY_ON_GOLEM_SHUTDOWN_DEADLINE
        check_seconds = int(RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds())

        time.sleep(check_seconds)
        while datetime.now() < wait_deadline:
            webserver_serviceable = self.is_webserver_serviceable()
            if webserver_serviceable is None:
                cli_logger.print("Previous webserver instance shutdown done")
                return

            cli_logger.print(
                "Previous webserver instance is not yet shutdown, "
                "waiting additional `{}` seconds...",
                check_seconds,
            )
            time.sleep(check_seconds)

        cli_logger.abort(
            "Previous webserver instance is still running! Deadline of `{}` reached.",
            RAY_ON_GOLEM_START_DEADLINE,
        )

    def create_cluster(
        self,
        cluster_config: Dict[str, Any],
    ) -> CreateClusterResponseData:
        return self._make_request(
            url=settings.URL_CREATE_CLUSTER,
            request_data=models.CreateClusterRequestData(**cluster_config),
            response_model=models.CreateClusterResponseData,
            error_message="Couldn't create cluster",
        )

    def request_nodes(
        self, node_config: Dict[str, Any], count: int, tags: models.Tags
    ) -> List[models.NodeId]:
        response = self._make_request(
            url=settings.URL_REQUEST_NODES,
            request_data=models.RequestNodesRequestData(
                node_config=node_config,
                count=count,
                tags=tags,
            ),
            response_model=models.RequestNodesResponseData,
            error_message="Couldn't request nodes",
        )

        return response.requested_nodes

    def terminate_node(self, node_id: models.NodeId) -> Dict[models.NodeId, Dict]:
        response = self._make_request(
            url=settings.URL_TERMINATE_NODE,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.TerminateNodeResponseData,
            error_message="Couldn't terminate node",
        )

        return response.terminated_nodes

    def get_cluster_state(self) -> Dict[models.NodeId, models.NodeData]:
        response = self._make_request(
            url=settings.URL_GET_CLUSTER_DATA,
            request_data=models.GetClusterDataRequestData(),
            response_model=models.GetClusterDataResponseData,
            error_message="Couldn't get cluster data",
        )

        return response.cluster_data

    def non_terminated_nodes(self, tag_filters: models.Tags) -> List[models.NodeId]:
        response = self._make_request(
            url=settings.URL_NON_TERMINATED_NODES,
            request_data=models.NonTerminatedNodesRequestData(
                tags=tag_filters,
            ),
            response_model=models.NonTerminatedNodesResponseData,
            error_message="Couldn't get non terminated nodes",
        )

        return response.nodes_ids

    def is_running(self, node_id: models.NodeId) -> bool:
        response = self._make_request(
            url=settings.URL_IS_RUNNING,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.IsRunningResponseData,
            error_message="Couldn't check if node is running",
        )

        return response.is_running

    def is_terminated(self, node_id: models.NodeId) -> bool:
        response = self._make_request(
            url=settings.URL_IS_TERMINATED,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.IsTerminatedResponseData,
            error_message="Couldn't check if node is terminated",
        )

        return response.is_terminated

    def get_node_tags(self, node_id: models.NodeId) -> models.Tags:
        response = self._make_request(
            url=settings.URL_NODE_TAGS,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.GetNodeTagsResponseData,
            error_message="Couldn't get node tags",
        )

        return response.tags

    def get_node_internal_ip(self, node_id: models.NodeId) -> str:
        response = self._make_request(
            url=settings.URL_INTERNAL_IP,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.GetNodeIpAddressResponseData,
            error_message="Couldn't get node internal_ip",
        )

        return response.ip_address

    def set_node_tags(self, node_id: models.NodeId, tags: models.Tags) -> None:
        self._make_request(
            url=settings.URL_SET_NODE_TAGS,
            request_data=models.SetNodeTagsRequestData(
                node_id=node_id,
                tags=tags,
            ),
            response_model=models.EmptyResponseData,
            error_message="Couldn't set tags for node",
        )

    def get_ssh_proxy_command(self, node_id: str) -> str:
        response = self._make_request(
            url=settings.URL_GET_SSH_PROXY_COMMAND,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.GetSshProxyCommandResponseData,
            error_message="Couldn't get ssh proxy command",
        )

        return response.ssh_proxy_command

    def get_or_create_default_ssh_key(self, cluster_name: str) -> str:
        response = self._make_request(
            url=settings.URL_GET_OR_CREATE_DEFAULT_SSH_KEY,
            request_data=models.GetOrCreateDefaultSshKeyRequestData(
                cluster_name=cluster_name,
            ),
            response_model=models.GetOrCreateDefaultSshKeyResponseData,
            error_message="Couldn't get or create default ssh key",
        )

        return response.ssh_key_base64

    def shutdown_webserver(self) -> models.ShutdownState:
        response = self._make_request(
            url=settings.URL_SELF_SHUTDOWN,
            request_data=models.SelfShutdownRequestData(),
            response_model=models.SelfShutdownResponseData,
            error_message="Couldn't send a self-shutdown request",
        )

        return response.shutdown_state

    def get_webserver_status(self) -> Optional[models.WebserverStatus]:
        try:
            return self._make_request(
                url=settings.URL_STATUS,
                response_model=models.WebserverStatus,
                method="GET",
            )
        except RayOnGolemClientError:
            return None

    def is_webserver_serviceable(self) -> Optional[bool]:
        status = self.get_webserver_status()
        return not status.shutting_down if status else None

    def _make_request(
        self,
        *,
        url: str,
        response_model: Type[TResponseModel],
        request_data: Optional[BaseModel] = None,
        error_message: str = "",
        method: str = "POST",
    ) -> TResponseModel:
        response = self._session.request(
            method, str(self._base_url / url.lstrip("/")),
            data=request_data.json() if request_data else None,
        )

        if response.status_code != 200:
            raise RayOnGolemClientError(
                f"{error_message or f'Request failed: {url}'}: {response.text}"
            )

        try:
            return response_model.parse_raw(response.text)
        except ValidationError as e:
            raise RayOnGolemClientValidationError(
                "Couldn't validate response data",
            ) from e
