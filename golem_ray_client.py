from typing import Any

import requests

NODE_ID = str
CLUSTER_ID = str


class GolemRayClientException(Exception):
    pass


class GolemRayClient:
    def __init__(self, golem_ray_url: str) -> None:
        self.golem_ray_url = golem_ray_url
        self.session = requests.Session()

        self._cluster_id = None

    def create_cluster(self) -> CLUSTER_ID:
        response = self.session.post(f"{self.golem_ray_url}/create_cluster")
        if response.status_code != 201:
            raise GolemRayClientException(
                f"Couldn't create cluster, response status_code: {response.status_code}, text: {response.text}"
            )
        cluster_id = response.json()["cluster_id"]
        self._cluster_id = cluster_id

        return cluster_id

    def non_terminated_nodes(self) -> list[NODE_ID]:
        ...

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

    def create_nodes(self, cluster_id: CLUSTER_ID, count: int) -> dict[NODE_ID, dict]:
        response = self.session.post(
            f"{self.golem_ray_url}/{cluster_id}/create_nodes",
            data={
                "count": count,
            }
        )
        if response.status_code != 201:
            raise GolemRayClientException(
                f"Couldn't create node, response status_code: {response.status_code}, text: {response.text}"
            )

        return response.json()["nodes"]
