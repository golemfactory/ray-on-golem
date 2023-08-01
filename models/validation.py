from ipaddress import IPv4Address
from typing import List, Dict

from pydantic.main import BaseModel

from models.types import Node, NodeID


class GetNodeRequest(BaseModel):
    node_id: int


class SingleNodeRequest(BaseModel):
    node_id: int


class CreateClusterRequest(BaseModel):
    image_hash: str
    network: str
    budget: int
    num_workers: int = 4


class NonTerminatedNodesRequest(BaseModel):
    tags: Dict


class CreateNodesRequest(BaseModel):
    count: int
    tags: Dict


class DeleteNodesRequest(BaseModel):
    node_ids: List[NodeID]


class SetNodeTagsRequest(BaseModel):
    node_id: NodeID
    tags: Dict


class CreateClusterResponse(BaseModel):
    nodes: List[NodeID]


class CreateNodesResponse(BaseModel):
    nodes: Dict[str, Dict]


class GetNodeResponse(BaseModel):
    node: Node


class GetNodesResponse(BaseModel):
    nodes: List[NodeID]


class IsRunningResponse(BaseModel):
    is_running: bool


class IsTerminatedResponse(BaseModel):
    is_terminated: bool


class GetNodeTagsResponse(BaseModel):
    tags: Dict


class GetNodeIpAddressResponse(BaseModel):
    ip_address: IPv4Address
