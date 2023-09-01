from http import HTTPStatus
from ipaddress import IPv4Address
from typing import Dict, List, Tuple, Type, TypeVar

import requests
from pydantic import BaseModel, ValidationError
from yarl import URL

from golem_ray.client.exceptions import GolemRayClientError, GolemRayClientValidationError
from golem_ray.server import models, settings

TResponseModel = TypeVar("TResponseModel")


class GolemRayClient:
    def __init__(self, base_url: URL) -> None:
        self._base_url = base_url

        self._session = requests.Session()

    def _make_request(
        self,
        *,
        url: str,
        request_data: BaseModel,
        response_model: Type[TResponseModel],
        error_message: str,
    ) -> TResponseModel:
        response = self._session.post(self._base_url / url.lstrip("/"), data=request_data.json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientError(f"{error_message}: {response.text}")

        try:
            return response_model.parse_raw(response.text)
        except ValidationError as e:
            raise GolemRayClientValidationError(
                "Couldn't validate response data",
            ) from e

    def get_running_or_create_cluster(
        self, image_url: URL, image_hash: str, network: str, budget: int
    ) -> List[models.NodeId]:
        response = self._make_request(
            url=settings.URL_CREATE_CLUSTER,
            request_data=models.CreateClusterRequestData(
                image_url=str(image_url),
                image_hash=image_hash,
                network=network,
                budget=budget,
            ),
            response_model=models.CreateClusterResponseData,
            request_data=request_data,
            error_message="Couldn't create cluster",
        )

    def non_terminated_nodes(self, tag_filters: models.Tags) -> List[models.NodeId]:
        response = self._make_request(
            url=settings.URL_GET_NODES,
            request_data=models.NonTerminatedNodesRequestData(
                tags=tag_filters,
            ),
            response_model=models.GetNodesResponseData,
            error_message="Couldn't get non terminated nodes",
        )

        return response.nodes

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

    def get_node_internal_ip(self, node_id: models.NodeId) -> IPv4Address:
        response = self._make_request(
            url=settings.URL_INTERNAL_IP,
            response_model=models.GetNodeIpAddressResponseData,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
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

    def terminate_node(self, node_id: models.NodeId) -> None:
        self.terminate_nodes([node_id])

    def terminate_nodes(self, node_ids: List[models.NodeId]) -> None:
        self._make_request(
            url=settings.URL_TERMINATE_NODES,
            request_data=models.DeleteNodesRequestData(
                node_ids=node_ids,
            ),
            response_model=models.EmptyResponseData,
            error_message="Couldn't terminate nodes",
        )

    def create_nodes(self, count: int, tags: models.Tags) -> Dict[models.NodeId, models.Node]:
        response = self._make_request(
            url=settings.URL_CREATE_NODES,
            request_data=models.CreateNodesRequestData(
                count=count,
                tags=tags,
            ),
            response_model=models.CreateNodesResponseData,
            error_message="Couldn't create node",
        )

        return response.nodes

    def get_ssh_proxy_command(self, node_id: str) -> str:
        response: models.GetSshProxyCommandResponseData = self._make_request(
            url=settings.URL_GET_SSH_PROXY_COMMAND,
            request_data=models.SingleNodeRequestData(
                node_id=node_id,
            ),
            response_model=models.GetSshProxyCommandResponseData,
            error_message="Cound't get ssh proxy command",
        )

        return response.ssh_proxy_command

    def get_head_node_ip(self) -> IPv4Address:
        response: models.GetNodeIpAddressResponseData = self._make_request(
            url=settings.URL_GET_HEAD_NODE_IP,
            request_data=models.EmptyRequestData(),
            response_model=models.GetNodeIpAddressResponseData,
            error_message="Couldn't get head node ip address",
        )

        return response.ip_address

    def get_image_url_from_hash(self, image_hash: str) -> URL:
        response: models.GetImageUrlFromHashResponseData = self._make_request(
            url=settings.URL_GET_IMAGE_URL_FROM_HASH,
            request_data=models.GetImageUrlFromHashRequestData(image_hash=image_hash),
            response_model=models.GetImageUrlFromHashResponseData,
            error_message="Couldn't get image url from given hash",
        )

        return URL(response.url)

    def get_image_url_and_hash_from_tag(self, image_tag: str) -> Tuple[URL, str]:
        response: models.GetImageUrlAndHashFromTagResponseData = self._make_request(
            url=settings.URL_GET_IMAGE_URL_AND_HASH_FROM_TAG,
            request_data=models.GetImageUrlAndHashFromTagRequestData(image_tag=image_tag),
            response_model=models.GetImageUrlAndHashFromTagResponseData,
            error_message="Couldn't get image url and hash from given tag",
        )

        return URL(response.url), response.image_hash
