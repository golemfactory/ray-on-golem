from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, List, Optional

from golem_core.core.activity_api import Activity
from pydantic import BaseModel

NodeID = int
ClusterID = str


class NodeState(Enum):
    pending = 'pending'
    running = 'running'
    stopping = 'stopping'


class Node(BaseModel):
    node_id: NodeID
    state: NodeState
    tags: Dict
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address]


class ClusterNode(BaseModel):
    node_id: int
    activity: Optional[Activity]
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address]
    state: Optional[NodeState]
    connection_uri: Optional[str]
    tags: Dict = {}

    class Config:
        arbitrary_types_allowed = True


class GetNodeRequestData(BaseModel):
    node_id: int


class SingleNodeRequestData(BaseModel):
    node_id: int


class CreateClusterRequestData(BaseModel):
    image_hash: str
    network: str
    budget: int
    num_workers: int = 4


class NonTerminatedNodesRequestData(BaseModel):
    tags: Dict


class CreateNodesRequestData(BaseModel):
    count: int
    tags: Dict


class DeleteNodesRequestData(BaseModel):
    node_ids: List[NodeID]


class SetNodeTagsRequestData(BaseModel):
    node_id: NodeID
    tags: Dict


class CreateClusterResponseData(BaseModel):
    nodes: List[NodeID]


class CreateNodesResponseData(BaseModel):
    nodes: Dict[str, Dict]


class GetNodeResponseData(BaseModel):
    node: Node


class GetNodesResponseData(BaseModel):
    nodes: List[NodeID]


class IsRunningResponseData(BaseModel):
    is_running: bool


class IsTerminatedResponseData(BaseModel):
    is_terminated: bool


class GetNodeTagsResponseData(BaseModel):
    tags: Dict


class GetNodeIpAddressResponseData(BaseModel):
    ip_address: IPv4Address


class EmptyResponseData(BaseModel):
    pass

class GetNodeProxyCommandResponseData(BaseModel):
    proxy_command: str