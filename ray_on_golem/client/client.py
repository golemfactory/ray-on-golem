from typing import Any, Dict, List, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from yarl import URL

from ray_on_golem.client.exceptions import RayOnGolemClientError, RayOnGolemClientValidationError
from ray_on_golem.server import models, settings

TResponseModel = TypeVar("TResponseModel")


class RayOnGolemClient:
    def __init__(self, port: int) -> None:
        self._base_url = URL("http://127.0.0.1").with_port(port)

        self._session = requests.Session()

    def create_cluster(
        self,
        cluster_config: Dict[str, Any],
    ) -> None:

        request_data = models.CreateClusterRequestData(**cluster_config)

        self._make_request(
            url=settings.URL_CREATE_CLUSTER,
            request_data=request_data,
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

    def shutdown_webserver(self) -> models.ShutdownState:
        response = self._make_request(
            url=settings.URL_SELF_SHUTDOWN,
            request_data=models.SelfShutdownRequestData(),
            response_model=models.SelfShutdownResponseData,
            error_message="Couldn't send a self-shutdown request",
        )

        return response.shutdown_state

    def is_webserver_running(self) -> bool:
        try:
            response = requests.get(
                str(self._base_url / settings.URL_HEALTH_CHECK.lstrip("/")),
                timeout=settings.RAY_ON_GOLEM_CHECK_DEADLINE.total_seconds(),
            )
        except requests.ConnectionError:
            return False
        else:
            return response.status_code == 200 and response.text == "ok"

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

        if response.status_code != 200:
            raise RayOnGolemClientError(f"{error_message}: {response.text}")

        try:
            return response_model.parse_raw(response.text)
        except ValidationError as e:
            raise RayOnGolemClientValidationError(
                "Couldn't validate response data",
            ) from e
