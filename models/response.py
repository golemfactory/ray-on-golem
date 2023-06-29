from typing import List

from pydantic.main import BaseModel

from models.types import ClusterId, Node


class CreateClusterResponse(BaseModel):
    # cluster_id: CLUSTER_ID
    pass


class CreateNodesResponse(BaseModel):
    nodes: List[Node]


class GetNodeResponse(BaseModel):
    node: Node


class GetNodesResponse(BaseModel):
    nodes: List[Node]
