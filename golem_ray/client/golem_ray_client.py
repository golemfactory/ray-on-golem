from http import HTTPStatus
from ipaddress import IPv4Address
from typing import List, Dict

import requests
from pydantic.error_wrappers import ValidationError

from golem_ray.client.exceptions import GolemRayClientException, GolemRayClientValidationException
from golem_ray.server.consts.urls import GolemRayURLs
from golem_ray.server.models.models import SingleNodeRequestData, CreateClusterRequestData, \
    NonTerminatedNodesRequestData, CreateNodesRequestData, DeleteNodesRequestData, SetNodeTagsRequestData, \
    CreateClusterResponseData, CreateNodesResponseData, GetNodesResponseData, IsRunningResponseData, \
    IsTerminatedResponseData, GetNodeTagsResponseData, GetNodeIpAddressResponseData, EmptyResponseData, NodeID, \
    ClusterID


class GolemRayClient:
    def __init__(self, base_url) -> None:
        self.session = requests.Session()
        self._cluster_id = None
        self._deleted_nodes: set[NodeID] = set()
        self.BASE_URL = base_url

    def _request(self,
                 url,
                 response_model,
                 request_data,
                 message):

        response = self.session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message=message,
                response=response
            )

        try:
            parsed_response = response_model.parse_raw(response.text)
            return parsed_response
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't validate response data",
                response=response,
                expected=response_model
            )

    def get_running_or_create_cluster(self, image_hash: str, network: str, budget: int) -> None:
        url = self.BASE_URL / GolemRayURLs.CREATE_CLUSTER
        request_data = CreateClusterRequestData(
            image_hash=image_hash,
            network=network,
            budget=budget,
        )

        self._request(url,
                      response_model=CreateClusterResponseData,
                      request_data=request_data,
                      message="Couldn't create cluster")

    def non_terminated_nodes(self, tag_filters) -> List[NodeID]:
        url = self.BASE_URL / GolemRayURLs.GET_NODES
        request_data = NonTerminatedNodesRequestData(tags=tag_filters)

        response: GetNodesResponseData = (
            self._request(url,
                          response_model=GetNodesResponseData,
                          request_data=request_data,
                          message="Couldn't get non terminated nodes"))

        return response.nodes

    def is_running(self, node_id: NodeID) -> bool:
        url = self.BASE_URL / GolemRayURLs.IS_RUNNING

        response: IsRunningResponseData = (
            self._request(url,
                          response_model=IsRunningResponseData,
                          request_data=SingleNodeRequestData(node_id=node_id),
                          message="Couldn't check if node is running"))

        return response.is_running

    def is_terminated(self, node_id: NodeID) -> bool:
        url = self.BASE_URL / GolemRayURLs.IS_TERMINATED

        response: IsTerminatedResponseData = (
            self._request(url,
                          response_model=IsTerminatedResponseData,
                          request_data=SingleNodeRequestData(node_id=node_id),
                          message="Couldn't check if node is terminated"))

        return response.is_terminated

    def get_node_tags(self, node_id) -> dict:
        url = self.BASE_URL / GolemRayURLs.NODE_TAGS

        response: GetNodeTagsResponseData = (
            self._request(url,
                          response_model=GetNodeTagsResponseData,
                          request_data=SingleNodeRequestData(node_id=node_id),
                          message="Couldn't get node tags"))

        return response.tags

    def get_node_internal_ip(self, node_id: NodeID) -> IPv4Address:
        url = self.BASE_URL / GolemRayURLs.INTERNAL_IP

        response: GetNodeIpAddressResponseData = (
            self._request(url,
                          response_model=GetNodeIpAddressResponseData,
                          request_data=SingleNodeRequestData(node_id=node_id),
                          message="Couldn't get node internal_ip"))

        return response.ip_address

    def set_node_tags(self, node_id: NodeID, tags: dict) -> None:
        url = self.BASE_URL / GolemRayURLs.SET_NODE_TAGS
        request_data = SetNodeTagsRequestData(node_id=node_id, tags=tags)

        response = self._request(url,
                                 response_model=EmptyResponseData,
                                 request_data=request_data,
                                 message="Couldn't set tags for node")

    def terminate_node(self, node_id: NodeID) -> None:
        self.terminate_nodes([node_id])

    def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        url = self.BASE_URL / GolemRayURLs.TERMINATE_NODES
        request_data = DeleteNodesRequestData(node_ids=node_ids)

        self._request(url,
                      response_model=EmptyResponseData,
                      request_data=request_data,
                      message="Couldn't terminate nodes")

    def create_nodes(self, cluster_id: ClusterID, count: int, tags: Dict) -> dict[str, dict]:
        url = self.BASE_URL / GolemRayURLs.CREATE_NODES
        request_data = CreateNodesRequestData(count=count, tags=tags)

        response: CreateNodesResponseData \
            = self._request(url,
                            response_model=CreateNodesResponseData,
                            request_data=request_data,
                            message="Couldn't create node")

        return response.nodes
