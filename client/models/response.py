from ipaddress import IPv4Address

from pydantic.main import BaseModel

from client.models.types import CLUSTER_ID, NODE_ID, Node


class CreateClusterResponse(BaseModel):
    cluster_id: CLUSTER_ID


class CreateNodesResponse(BaseModel):
    nodes: list[Node]
