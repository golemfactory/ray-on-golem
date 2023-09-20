# TODO: Consider moving this package to ray_on_golem/provider/client because of cli_logger usage
import subprocess
from functools import lru_cache
from http import HTTPStatus
from time import sleep
from typing import Any, Dict, List, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from ray.autoscaler._private.cli_logger import cli_logger
from yarl import URL

from ray_on_golem.client.exceptions import RayOnGolemClientError, RayOnGolemClientValidationError
from ray_on_golem.server import models, settings
from ray_on_golem.server.models import NodeConfigData, ShutdownState
from ray_on_golem.server.settings import RAY_ON_GOLEM_PATH, URL_HEALTH_CHECK
from ray_on_golem.utils import is_running_on_golem_network

TResponseModel = TypeVar("TResponseModel")


class RayOnGolemClient:
    def __init__(self, base_url: URL) -> None:
        self._base_url = base_url

        self._session = requests.Session()

        if not is_running_on_golem_network():
            self._start_webserver()

    @classmethod
    @lru_cache()
    def get_instance(cls, port: int) -> "RayOnGolemClient":
        url = cls.get_url(port)
        return RayOnGolemClient(url)

    @staticmethod
    def get_url(port: int) -> URL:
        return URL("http://127.0.0.1").with_port(port)

    def get_running_or_create_cluster(
        self,
        network: str,
        budget: int,
        node_config: NodeConfigData,
        ssh_private_key: str,
    ) -> None:
        self._make_request(
            url=settings.URL_CREATE_CLUSTER,
            request_data=models.CreateClusterRequestData(
                network=network,
                budget=budget,
                node_config=node_config,
                ssh_private_key=ssh_private_key,
            ),
            response_model=models.EmptyResponseData,
            error_message="Couldn't create cluster",
        )

    def create_nodes(
        self, node_config: Dict[str, Any], count: int, tags: models.Tags
    ) -> Dict[models.NodeId, Dict]:
        response = self._make_request(
            url=settings.URL_CREATE_NODES,
            request_data=models.CreateNodesRequestData(
                node_config=node_config,
                count=count,
                tags=tags,
            ),
            response_model=models.CreateNodesResponseData,
            error_message="Couldn't create node",
        )

        return response.created_nodes

    def terminate_node(self, node_id: models.NodeId) -> Dict[models.NodeId, Dict]:
        response = self._make_request(
            url=settings.URL_TERMINATE_NODE,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.TerminateNodeResponseData,
            error_message="Couldn't terminate node",
        )

        self._stop_webserver()

        return response.terminated_nodes

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

        return str(response.ip_address)

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

    def _make_request(
        self,
        *,
        url: str,
        request_data: BaseModel,
        response_model: Type[TResponseModel],
        error_message: str,
    ) -> TResponseModel:
        response = self._session.post(
            str(self._base_url / url.lstrip("/")), data=request_data.json()
        )

        if response.status_code != HTTPStatus.OK:
            raise RayOnGolemClientError(f"{error_message}: {response.text}")

        try:
            return response_model.parse_raw(response.text)
        except ValidationError as e:
            raise RayOnGolemClientValidationError(
                "Couldn't validate response data",
            ) from e

    def _start_webserver(self) -> None:
        with cli_logger.group("Ray On Golem webserver"):
            if self._is_webserver_running():
                cli_logger.print("Webserver is already running")
                return

            cli_logger.print("Starting webserver...")
            subprocess.Popen(
                [RAY_ON_GOLEM_PATH, "-p", str(self._base_url.port), "--self-shutdown"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            for _ in range(10):
                sleep(2)

                if self._is_webserver_running():
                    cli_logger.print("Starting webserver done")
                    return

                cli_logger.print("Webserver is not yet running, waiting additional 2 seconds...")

            cli_logger.abort("Starting webserver failed!")

    def _stop_webserver(self) -> None:
        with cli_logger.group("Ray On Golem webserver"):
            if not self._is_webserver_running():
                cli_logger.print("Webserver is already stopped")
                return

            cli_logger.print("Requesting webserver stop...")

            response = self._make_request(
                url=settings.URL_SELF_SHUTDOWN,
                request_data=models.SelfShutdownRequestData(),
                response_model=models.SelfShutdownResponseData,
                error_message="Couldn't send self shutdown request",
            )

            if response.shutdown_state == ShutdownState.NOT_ENABLED:
                cli_logger.print("No need to stop webserver, as it was ran externally")
                return
            elif response.shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
                cli_logger.print("No need to stop webserver, as cluster is not empty")
                return

            cli_logger.print("Requesting webserver done, will stop soon")

    def _is_webserver_running(self) -> bool:
        try:
            response = self._session.get(
                str(self._base_url / URL_HEALTH_CHECK.lstrip("/")), timeout=2
            )
        except requests.ConnectionError:
            return False
        else:
            return response.status_code == HTTPStatus.OK and response.text == "ok"
