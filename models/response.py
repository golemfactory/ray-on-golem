from typing import List

from pydantic.main import BaseModel

from models.types import ClusterID, Node


class CreateClusterResponse(BaseModel):
    # cluster_id: ClusterID
    pass


class CreateNodesResponse(BaseModel):
    nodes: List[Node]


class GetNodeResponse(BaseModel):
    node: Node


class GetNodesResponse(BaseModel):
    nodes: List[Node]
