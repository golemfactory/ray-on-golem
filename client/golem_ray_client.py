from http import HTTPStatus

import requests
from pydantic.error_wrappers import ValidationError

from client.models.request import CreateNodesRequest
from client.models.response import CreateClusterResponse, CreateNodesResponse
from client.models.types import CLUSTER_ID, NODE_ID, Node


class GolemRayClientException(Exception):
    pass


class GolemRayClient:
    def __init__(self, golem_ray_url: str) -> None:
        self.golem_ray_url = golem_ray_url
        self.session = requests.Session()

        self._cluster_id = None

    def _build_url(self, path: str) -> str:
        return '/'.join([self.golem_ray_url.rstrip('/'), path.lstrip('/')])

    def create_cluster(self) -> CLUSTER_ID:
        url = self._build_url("create_cluster")
        response = self.session.post(url)

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

        # try:
        #     parsed_data = CreateClusterResponse(**response.json())
        # except ValidationError:
        #     raise
        # else:
        #     cluster_id = parsed_data.cluster_id
        #     self._cluster_id = cluster_id
        #     return cluster_id

    def is_running(self, node_id: NODE_ID) -> bool:
        ...

    def is_terminated(self, node_id: NODE_ID) -> bool:
        ...

    def node_tags(self, node_id: NODE_ID) -> dict:
        ...

    def external_ip(self, node_id: NODE_ID) -> str:
        ...

    def internal_ip(self, node_id: NODE_ID) -> str:
        ...

    def set_node_tags(self, node_id: NODE_ID, tags: dict) -> None:
        ...

    def terminate_node(self, node_id: NODE_ID) -> None:
        ...

    def terminate_nodes(self, node_id: list[NODE_ID]) -> None:
        ...

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
