from http import HTTPStatus
from ipaddress import IPv4Address

import requests
from pydantic.error_wrappers import ValidationError
from ray.util.state.common import NodeState

from models.request import CreateNodesRequest, CreateClusterRequest, DeleteNodesRequest
from models.response import CreateClusterResponse, CreateNodesResponse, GetNodesResponse, GetNodeResponse
from models.types import CLUSTER_ID, NODE_ID, Node, NodeState


class GolemRayClientException(Exception):
    pass


class GolemRayClient:
    DEFAULT_IMAGE_HASH = "83a7145df831d9b62508a912485d2e9ac03e70df328e7142a899c2bf"

    def __init__(self, golem_ray_url: str) -> None:
        self.golem_ray_url = golem_ray_url
        self.session = requests.Session()

        self._cluster_id = None

    def _build_url(self, path: str) -> str:
        return '/'.join([self.golem_ray_url.rstrip('/'), path.lstrip('/')])

    def create_cluster(self) -> CLUSTER_ID:
        url = self._build_url("create_demand")
        data = CreateClusterRequest(image_hash=self.DEFAULT_IMAGE_HASH).dict()
        response = self.session.post(url, data=data)

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create cluster, response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = CreateClusterResponse(**response.json())
        except ValidationError:
            raise
        else:
            cluster_id = parsed_data.cluster_id
            self._cluster_id = cluster_id
            return cluster_id

    def non_terminated_nodes(self) -> list[NODE_ID]:
        url = self._build_url(f"nodes/{self._cluster_id}")
        response = self.session.get(url)

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                "Couldn't fetch nodes from cluster, "
                f"response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = GetNodesResponse(**response.json())
        except ValidationError:
            raise
        else:
            nodes = parsed_data.nodes
            return [node.node_id for node in nodes]

    def is_running(self, node_id: NODE_ID) -> bool:
        return self._fetch_node(node_id).state == NodeState.running

    def is_terminated(self, node_id: NODE_ID) -> bool:
        return self._fetch_node(node_id).state not in [NodeState.pending, NodeState.running]

    def node_tags(self, node_id: NODE_ID) -> dict:
        ...

    def external_ip(self, node_id: NODE_ID) -> IPv4Address:
        return self._fetch_node(node_id).external_ip

    def internal_ip(self, node_id: NODE_ID) -> IPv4Address:
        return self._fetch_node(node_id).internal_ip

    def _fetch_node(self, node_id: NODE_ID) -> Node:
        url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        response = self.session.get(url)

        if response.status_code == HTTPStatus.OK:
            try:
                parsed_data = GetNodeResponse(**response.json())
            except ValidationError:
                raise
            else:
                return parsed_data.node

        raise GolemRayClientException(
            "Couldn't fetch node from cluster, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def set_node_tags(self, node_id: NODE_ID, tags: dict) -> None:
        ...

    def terminate_node(self, node_id: NODE_ID) -> None:
        url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        response = self.session.delete(url)

        if response.status_code == HTTPStatus.OK:
            return

        raise GolemRayClientException(
            "Couldn't delete node, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def terminate_nodes(self, node_ids: list[NODE_ID]) -> None:
        url = self._build_url(f"{self._cluster_id}/nodes")
        data = DeleteNodesRequest(node_ids=node_ids).dict()
        response = self.session.delete(url, data=data)

        if response.status_code == HTTPStatus.OK:
            return

        raise GolemRayClientException(
            "Couldn't delete nodes, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def create_nodes(self, cluster_id: CLUSTER_ID, count: int) -> list[Node]:
        url = self._build_url(f"{cluster_id}/create_nodes")
        data = CreateNodesRequest(count=count).dict()
        response = self.session.post(url, data=data)

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create node, response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = CreateNodesResponse(**response.json())
        except ValidationError:
            raise
        else:
            nodes = parsed_data.nodes
            return nodes
