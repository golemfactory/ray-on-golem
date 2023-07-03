import json
from http import HTTPStatus

import requests
from pydantic.error_wrappers import ValidationError

from models.request import CreateNodesRequest, CreateClusterRequest, DeleteNodesRequest
from models.response import CreateNodesResponse, GetNodesResponse, GetNodeResponse
from models.types import ClusterId, NodeId, Node


class GolemRayClientException(Exception):
    pass


class GolemRayClient:

    def __init__(self, golem_ray_url: str) -> None:
        self.golem_ray_url = golem_ray_url
        self.session = requests.Session()

        self._cluster_id = None

    def _build_url(self, path: str) -> str:
        return '/'.join([self.golem_ray_url.rstrip('/'), 'golem', path.lstrip('/')])

    def create_cluster(self, image_hash: str) -> None:  # -> ClusterId:
        url = self._build_url("create_cluster")
        data = CreateClusterRequest(image_hash=image_hash).dict()
        json_data = json.dumps(data)
        print(f"POST {url} data={json_data}")
        response = self.session.post(url, data=json_data, headers={'Content-type': 'application/json'})

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create cluster details: \n"
                f"request url: {url}, data: {data}\n"
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

    def non_terminated_nodes(self) -> list[NodeId]:
        # url = self._build_url(f"nodes/{self._cluster_id}")
        url = self._build_url(f"nodes")
        print(f"GET {url}")
        response = self.session.get(url)

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                "Couldn't fetch nodes from cluster, "
                f"response status_code: {response.status_code}, text: {response.text}"
            )
        print(response.json())

        try:
            parsed_data = GetNodesResponse(**response.json())
        except ValidationError:
            raise GolemRayClientException(
                "Couldn't parse response from server, \n"
                f"{response.json() = }\n"
                f"expected {GetNodesResponse}"
            )
        else:
            nodes = parsed_data.nodes
            return [node.node_id for node in nodes]

    def node_tags(self, node_id: NodeId) -> dict:
        ...

    def fetch_node(self, node_id: NodeId) -> Node:
        # url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        url = self._build_url(f"nodes/{node_id}")
        print(f"GET {url}")
        response = self.session.get(url)

        if response.status_code == HTTPStatus.OK:
            try:
                parsed_data = GetNodeResponse(**response.json())
            except ValidationError:
                raise GolemRayClientException(
                    "Couldn't parse response from server, \n"
                    f"{response.json() = }\n"
                    f"expected {GetNodeResponse}"
                )
            else:
                return parsed_data.node

        raise GolemRayClientException(
            "Couldn't fetch node from cluster, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def set_node_tags(self, node_id: NodeId, tags: dict) -> None:
        ...

    def terminate_node(self, node_id: NodeId) -> None:
        # url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        url = self._build_url(f"nodes/{node_id}")
        print(f"DELETE {url}")
        response = self.session.delete(url)

        if response.status_code == HTTPStatus.OK:
            return

        raise GolemRayClientException(
            "Couldn't delete node, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def terminate_nodes(self, node_ids: list[NodeId]) -> None:
        # url = self._build_url(f"{self._cluster_id}/nodes")
        url = self._build_url(f"nodes")
        data = DeleteNodesRequest(node_ids=node_ids).dict()
        json_data = json.dumps(data)
        print(f"DELETE {url} data={json_data}")
        response = self.session.delete(url, json=json_data)

        if response.status_code == HTTPStatus.OK:
            return

        raise GolemRayClientException(
            "Couldn't delete nodes,\n"
            f"request url: {url}, data: {data}\n"
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def create_nodes(self, cluster_id: ClusterId, count: int) -> list[Node]:
        # url = self._build_url(f"{cluster_id}/create_nodes")
        url = self._build_url(f"create_nodes")
        data = CreateNodesRequest(count=count).dict()
        json_data = json.dumps(data)
        print(f"POST {url} data={json_data}")
        response = self.session.post(url, json=json_data)

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create node,\n"
                f"request url: {url}, data: {data}\n"
                f"response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = CreateNodesResponse(**response.json())
        except ValidationError:
            raise GolemRayClientException(
                "Couldn't parse response from server, \n"
                f"{response.json() = }\n"
                f"expected {CreateNodesResponse}"
            )
        else:
            nodes = parsed_data.nodes
            return nodes
