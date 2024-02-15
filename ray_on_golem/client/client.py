import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from ray.autoscaler._private.cli_logger import cli_logger  # noqa
from yarl import URL

from ray_on_golem.client.exceptions import RayOnGolemClientError, RayOnGolemClientValidationError
from ray_on_golem.server import models, settings
from ray_on_golem.server.models import CreateClusterResponseData

TResponseModel = TypeVar("TResponseModel")

logger = logging.getLogger(__name__)


class RayOnGolemClient:
    def __init__(self, port: int) -> None:
        self.port = port
        self.base_url = URL("http://127.0.0.1").with_port(self.port)
        self._session = requests.Session()

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
        logger.info(f"Terminating node %s", node_id)
        try:
            response = self._make_request(
                url=settings.URL_TERMINATE_NODE,
                request_data=models.SingleNodeRequestData(
                    node_id=node_id,
                ),
                response_model=models.TerminateNodeResponseData,
                error_message=f"Couldn't terminate node {node_id}",
            )
        except RayOnGolemClientError as e:
            if e.error_code == 400:
                logger.error(str(e))
                return {}
            else:
                raise

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

    def get_or_create_default_ssh_key(self, cluster_name: str) -> Tuple[str, str]:
        response = self._make_request(
            url=settings.URL_GET_OR_CREATE_DEFAULT_SSH_KEY,
            request_data=models.GetOrCreateDefaultSshKeyRequestData(
                cluster_name=cluster_name,
            ),
            response_model=models.GetOrCreateDefaultSshKeyResponseData,
            error_message="Couldn't get or create default ssh key",
        )

        return response.ssh_private_key_base64, response.ssh_public_key_base64

    def shutdown_webserver(
        self,
        shutdown_delay: timedelta,
        ignore_self_shutdown: bool = False,
        force_shutdown: bool = False,
    ) -> models.ShutdownState:
        response = self._make_request(
            url=settings.URL_SHUTDOWN,
            request_data=models.ShutdownRequestData(
                ignore_self_shutdown=ignore_self_shutdown,
                force_shutdown=force_shutdown,
                shutdown_delay=int(shutdown_delay.total_seconds()),
            ),
            response_model=models.ShutdownResponseData,
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
        try:
            response = self._session.request(
                method,
                str(self.base_url / url.lstrip("/")),
                data=request_data.json() if request_data else None,
            )
        except requests.ConnectionError as e:
            raise RayOnGolemClientError(f"{error_message or f'Connection failed: {url}'}: {e}")

        if response.status_code != 200:
            raise RayOnGolemClientError(
                f"{error_message or f'Request failed: {url}'}: {response.text}",
                error_code=response.status_code,
            )

        try:
            return response_model.parse_raw(response.text)
        except ValidationError as e:
            raise RayOnGolemClientValidationError(
                "Couldn't validate response data",
            ) from e
