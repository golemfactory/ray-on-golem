from http import HTTPStatus
from ipaddress import IPv4Address
from typing import List, Dict, Set, TypeVar

import requests
from pydantic.error_wrappers import ValidationError
from typing_extensions import Type
from yarl import URL

import golem_ray.server.config as config
import golem_ray.server.models as models
from golem_ray.client.exceptions import GolemRayClientException, GolemRayClientValidationException


ResponseModelType = TypeVar('ResponseModelType')


class GolemRayClient:
    def __init__(self, base_url: URL) -> None:
        self._session = requests.Session()
        self._cluster_id = None
        self._deleted_nodes: Set[models.NodeID] = set()
        self._base_url: URL = base_url

    def _request(self,
                 url_suffix: str,
                 response_model: Type[ResponseModelType],
                 request_data,
                 error_message) -> ResponseModelType:

        url = self._base_url.with_path(str(url_suffix))
        response = self._session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message=error_message,
                response=response
            )

        try:
            if response.text.strip() != '':
                parsed_response = response_model.parse_raw(response.text)
                return parsed_response
        except ValidationError:
            raise GolemRayClientValidationException(
                error_message="Couldn't validate response data",
                response=response,
                expected=response_model
            )

    def get_running_or_create_cluster(self, image_hash: str, network: str, budget: int) -> None:
        url = config.URL_CREATE_CLUSTER
        request_data = models.CreateClusterRequestData(
            image_hash=image_hash,
            network=network,
            budget=budget,
        )
        self._request(url,
                      response_model=models.CreateClusterResponseData,
                      request_data=request_data,
                      error_message="Couldn't create cluster")

    def non_terminated_nodes(self, tag_filters) -> List[models.NodeID]:
        url = config.URL_GET_NODES
        request_data = models.NonTerminatedNodesRequestData(tags=tag_filters)

        response: models.GetNodesResponseData = (
            self._request(url,
                          response_model=models.GetNodesResponseData,
                          request_data=request_data,
                          error_message="Couldn't get non terminated nodes"))

        return response.nodes

    def is_running(self, node_id: models.NodeID) -> bool:
        url = config.URL_IS_RUNNING

        response: models.IsRunningResponseData = (
            self._request(url,
                          response_model=models.IsRunningResponseData,
                          request_data=models.SingleNodeRequestData(node_id=node_id),
                          error_message="Couldn't check if node is running"))

        return response.is_running

    def is_terminated(self, node_id: models.NodeID) -> bool:
        url = config.URL_IS_TERMINATED

        response: models.IsTerminatedResponseData = (
            self._request(url,
                          response_model=models.IsTerminatedResponseData,
                          request_data=models.SingleNodeRequestData(node_id=node_id),
                          error_message="Couldn't check if node is terminated"))

        return response.is_terminated

    def get_node_tags(self, node_id) -> Dict:
        url = config.URL_NODE_TAGS

        response: models.GetNodeTagsResponseData = (
            self._request(url,
                          response_model=models.GetNodeTagsResponseData,
                          request_data=models.SingleNodeRequestData(node_id=node_id),
                          error_message="Couldn't get node tags"))

        return response.tags

    def get_node_internal_ip(self, node_id: models.NodeID) -> IPv4Address:
        url = config.URL_INTERNAL_IP

        response: models.GetNodeIpAddressResponseData = (
            self._request(url,
                          response_model=models.GetNodeIpAddressResponseData,
                          request_data=models.SingleNodeRequestData(node_id=node_id),
                          error_message="Couldn't get node internal_ip"))

        return response.ip_address

    def set_node_tags(self, node_id: models.NodeID, tags: Dict) -> None:
        url = config.URL_SET_NODE_TAGS
        request_data = models.SetNodeTagsRequestData(node_id=node_id, tags=tags)

        response = self._request(url,
                                 response_model=models.EmptyResponseData,
                                 request_data=request_data,
                                 error_message="Couldn't set tags for node")

    def terminate_node(self, node_id: models.NodeID) -> None:
        self.terminate_nodes([node_id])

    def terminate_nodes(self, node_ids: List[models.NodeID]) -> None:
        url = config.URL_TERMINATE_NODES
        request_data = models.DeleteNodesRequestData(node_ids=node_ids)

        self._request(url,
                      response_model=models.EmptyResponseData,
                      request_data=request_data,
                      error_message="Couldn't terminate nodes")

    def create_nodes(self, cluster_id: models.ClusterID, count: int, tags: Dict) -> Dict[str, Dict]:
        url = config.URL_CREATE_NODES
        request_data = models.CreateNodesRequestData(count=count, tags=tags)

        response: models.CreateNodesResponseData \
            = self._request(url,
                            response_model=models.CreateNodesResponseData,
                            request_data=request_data,
                            error_message="Couldn't create node")

        return response.nodes
