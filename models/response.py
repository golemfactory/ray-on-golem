from pydantic.main import BaseModel

from models.types import CLUSTER_ID, Node


class CreateClusterResponse(BaseModel):
    cluster_id: CLUSTER_ID


class CreateNodesResponse(BaseModel):
    nodes: list[Node]


class GetNodeResponse(BaseModel):
    node: Node


class GetNodesResponse(BaseModel):
    nodes: list[Node]
