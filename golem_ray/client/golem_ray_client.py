import json
from http import HTTPStatus
from typing import List, Dict

import requests
from pydantic.error_wrappers import ValidationError
from yarl import URL

from models.request import CreateNodesRequest, CreateClusterRequest, DeleteNodesRequest, SetNodeTagsRequest
from models.response import CreateNodesResponse, GetNodesResponse, GetNodeResponse
from models.types import ClusterID, NodeID, Node


class GolemRayClientException(Exception):
    pass


class GolemRayClient:

    def __init__(self, golem_ray_url: str) -> None:
        self.golem_ray_url = URL(golem_ray_url) / "golem"
        self.session = requests.Session()

        self._cluster_id = None
        self._deleted_nodes: set[NodeID] = set()

    def create_cluster(self, image_hash: str, network: str, budget: int) -> None:  # -> CLUSTER_ID:
        url = self.golem_ray_url / "create_cluster"
        json_data = CreateClusterRequest(
            image_hash=image_hash,
            network=network,
            budget=budget,
        ).json()

        print("\n/" + '=' * 100)
        print(f"POST {url} data={json_data}")

        response = self.session.post(url, data=json_data, headers={'Content-type': 'application/json'})

        print(json.dumps(response.json(), indent=2))
        print("\\" + '=' * 100 + '\n')

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create cluster details: \n"
                f"request url: {url}, json_data: {json_data}\n"
                f"response status_code: {response.status_code}, text: {response.text}"
            )

        # TODO: uncomment after server implements cluster_id
        # try:
        #     parsed_data = CreateClusterResponse(**response.json())
        # except ValidationError:
        #     raise
        # else:
        #     cluster_id = parsed_data.cluster_id
        #     self._cluster_id = cluster_id
        #     return cluster_id

    def non_terminated_nodes(self) -> List[NodeID]:
        # url = self._build_url(f"nodes/{self._cluster_id}")
        url = self.golem_ray_url / "nodes"

        print("\n/" + '=' * 100)
        print(f"GET {url}")

        response = self.session.get(url)

        print(json.dumps(response.json(), indent=2))
        print("\\" + '=' * 100 + '\n')

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                "Couldn't fetch nodes from cluster, "
                f"response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = GetNodesResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientException(
                "Couldn't parse response from server, \n"
                f"{response.json() = }\n"
                f"expected {GetNodesResponse}"
            )
        else:
            nodes = parsed_data.nodes
            return [node.node_id for node in nodes if node.node_id not in self._deleted_nodes]

    def fetch_node(self, node_id: NodeID) -> Node:
        # TODO: uncomment after server implements cluster_id
        # url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        url = self.golem_ray_url / "nodes" / node_id

        print("\n/" + '=' * 100)
        print(f"GET {url}")
        response = self.session.get(url)

        if response.status_code == HTTPStatus.OK:
            try:
                parsed_data = GetNodeResponse.parse_raw(response.text)
            except ValidationError:
                raise GolemRayClientException(
                    "Couldn't parse response from server, \n"
                    f"{response.json() = }\n"
                    f"expected {GetNodeResponse}"
                )
            else:
                print(json.dumps(response.json(), indent=2))
                print("\\" + '=' * 100 + '\n')
                return parsed_data.node

        raise GolemRayClientException(
            "Couldn't fetch node from cluster, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def set_node_tags(self, node_id: NodeID, tags: dict) -> None:
        url = self.golem_ray_url / "set_node_tags" / node_id
        json_data = SetNodeTagsRequest(tags=tags).json()

        print("\n/" + '=' * 100)
        print(f"PATCH {url} data={json_data}")

        response = self.session.patch(url, data=json_data, headers={'Content-type': 'application/json'})

        print(json.dumps(response.json(), indent=2))
        print("\\" + '=' * 100 + '\n')

        if response.status_code != HTTPStatus.OK:
            raise GolemRayClientException(
                f"Couldn't create node,\n"
                f"request url: {url}, data: {json_data}\n"
                f"response status_code: {response.status_code}, text: {response.text}"
            )

    def terminate_node(self, node_id: NodeID) -> None:
        return self.terminate_nodes([node_id])
        # url = self._build_url(f"{self._cluster_id}/nodes/{node_id}")
        url = self.golem_ray_url / "nodes" / node_id

        print("\n/" + '=' * 100)
        print(f"DELETE {url}")

        # TODO: uncomment after server implements deleting
        response = self.session.delete(url)

        print(f"{response.status_code = }")
        print("\\" + '=' * 100 + '\n')

        if response.status_code == HTTPStatus.OK:
            self._deleted_nodes.add(node_id)
            return

        raise GolemRayClientException(
            "Couldn't delete node, "
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def terminate_nodes(self, node_ids: List[NodeID]) -> None:
        # url = self._build_url(f"{self._cluster_id}/nodes")
        url = self.golem_ray_url / "nodes"
        json_data = DeleteNodesRequest(node_ids=node_ids).json()

        print("\n/" + '=' * 100)
        print(f"DELETE {url} data={json_data}")

        response = self.session.delete(url, data=json_data)

        print(f'{response.status_code = }')
        print("\\" + '=' * 100 + '\n')

        if response.status_code == HTTPStatus.NO_CONTENT:
            self._deleted_nodes.update(set(node_ids))
            return

        raise GolemRayClientException(
            "Couldn't delete nodes,\n"
            f"request url: {url}, data: {json_data}\n"
            f"response status_code: {response.status_code}, text: {response.text}"
        )

    def create_nodes(self, cluster_id: ClusterID, count: int, tags: Dict, head_node: bool = False) -> List[Node]:
        # TODO: uncomment after server implements cluster_id
        # url = self._build_url(f"{cluster_id}/create_nodes")
        if head_node:
            url = self.golem_ray_url / "head_nodes"
        else:
            url = self.golem_ray_url / "nodes"
        data = CreateNodesRequest(count=count, tags=tags).dict()
        json_data = json.dumps(data)

        print("\n/" + '=' * 100)
        print(f"POST {url} data={json_data!r}")

        response = self.session.post(url, data=json_data, headers={'Content-type': 'application/json'})

        print(json.dumps(response.json(), indent=2))
        print("\\" + '=' * 100 + '\n')

        if response.status_code != HTTPStatus.CREATED:
            raise GolemRayClientException(
                f"Couldn't create node,\n"
                f"request url: {url}, data: {data}\n"
                f"response status_code: {response.status_code}, text: {response.text}"
            )

        try:
            parsed_data = CreateNodesResponse.parse_raw(response.text)
        except ValidationError:
            raise GolemRayClientException(
                "Couldn't parse response from server, \n"
                f"{response.json() = }\n"
                f"expected {CreateNodesResponse}"
            )
        else:
            nodes = parsed_data.nodes
            return nodes
