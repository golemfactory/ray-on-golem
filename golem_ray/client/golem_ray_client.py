import json
from http import HTTPStatus
from ipaddress import IPv4Address
from typing import List, Dict

import requests
from pydantic.error_wrappers import ValidationError

from golem_ray.client.exceptions import GolemRayClientException, GolemRayClientValidationException
from models.types import ClusterID, NodeID
from models.urls import GolemRayURLs
from models.validation import (CreateNodesRequest, CreateClusterRequest, DeleteNodesRequest,
                               SetNodeTagsRequest, SingleNodeRequest, CreateNodesResponse,
                               GetNodesResponse, CreateClusterResponse, IsRunningResponse,
                               IsTerminatedResponse, GetNodeTagsResponse, GetNodeIpAddressResponse,
                               NonTerminatedNodesRequest)

golem_ray_urls = GolemRayURLs()

class GolemRayClient:

    def __init__(self) -> None:
        self.session = requests.Session()

        self._cluster_id = None
        self._deleted_nodes: set[NodeID] = set()

    def get_running_or_create_cluster(self, image_hash: str, network: str, budget: int) -> None:
        url = golem_ray_urls.CREATE_CLUSTER
        request_data = CreateClusterRequest(
            image_hash=image_hash,
            network=network,
            budget=budget,
        )

        response = self.session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                message=f"Couldn't create cluster details",
                response=response
            )

        try:
            parsed_response = CreateClusterResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't create cluster details",
                response=response,
                expected=CreateClusterResponse
            )

    def non_terminated_nodes(self, tag_filters) -> List[NodeID]:
        url = golem_ray_urls.GET_NODES
        request_data = NonTerminatedNodesRequest(tags=tag_filters)

        response = self.session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't fetch nodes from cluster",
                response=response
            )

        try:
            parsed_response = GetNodesResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=GetNodesResponse
            )
        else:
            return parsed_response.nodes

    def is_running(self, node_id: NodeID) -> bool:
        url = golem_ray_urls.IS_RUNNING

        response = self.session.post(url, data=SingleNodeRequest(node_id=node_id).json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't check node status",
                response=response
            )

        try:
            parsed_response = IsRunningResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=IsRunningResponse
            )
        else:
            return parsed_response.is_running

    def is_terminated(self, node_id: NodeID) -> bool:
        url = golem_ray_urls.IS_TERMINATED

        response = self.session.post(url, data=SingleNodeRequest(node_id=node_id).json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't check node status",
                response=response
            )

        try:
            parsed_response = IsTerminatedResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=IsTerminatedResponse
            )
        else:
            return parsed_response.is_terminated

    def get_node_tags(self, node_id) -> dict:
        url = golem_ray_urls.NODE_TAGS

        response = self.session.post(url, data=SingleNodeRequest(node_id=node_id).json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't check node status",
                response=response
            )

        try:
            parsed_response = GetNodeTagsResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=GetNodeTagsResponse
            )
        else:
            return parsed_response.tags

    def get_node_internal_ip(self, node_id: NodeID) -> IPv4Address:
        url = golem_ray_urls.INTERNAL_IP

        response = self.session.post(url, data=SingleNodeRequest(node_id=node_id).json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't check node status",
                response=response
            )

        try:
            parsed_response = GetNodeIpAddressResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=GetNodeIpAddressResponse
            )
        else:
            return parsed_response.ip_address

    def set_node_tags(self, node_id: NodeID, tags: dict) -> None:
        url = golem_ray_urls.SET_NODE_TAGS
        request_data = SetNodeTagsRequest(node_id=node_id, tags=tags)

        response = self.session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                message="Couldn't create node",
                response=response
            )

    def terminate_node(self, node_id: NodeID) -> None:
        return self.terminate_nodes([node_id])

    def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        url = golem_ray_urls.TERMINATE_NODES
        request_data = DeleteNodesRequest(node_ids=node_ids)

        response = self.session.post(url, data=request_data.json())

        if response.status_code == HTTPStatus.NO_CONTENT:
            self._deleted_nodes.update(set(node_ids))
            return

        raise GolemRayClientException(
            message="Couldn't delete nodes",
            response=response
        )

    def create_nodes(self, cluster_id: ClusterID, count: int, tags: Dict) -> dict[str, dict]:
        url = golem_ray_urls.CREATE_NODES
        request_data = CreateNodesRequest(count=count, tags=tags)

        response = self.session.post(url, data=request_data.json())

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                message="Couldn't create node",
                response=response
            )

        try:
            parsed_data = CreateNodesResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientValidationException(
                message="Couldn't parse response from server",
                response=response,
                expected=CreateNodesResponse
            )
        else:
            return parsed_data.nodes
