from enum import Enum
from ipaddress import IPv4Address
from typing import Dict, List, Optional

from golem_core.core.activity_api import Activity
from pydantic import BaseModel, Field

NodeId = int
Tags = Dict[str, str]


class NodeState(Enum):
    pending = "pending"
    running = "running"
    stopping = "stopping"


class Node(BaseModel):
    node_id: NodeId
    state: NodeState
    tags: Tags
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address] = None


class ClusterNode(BaseModel):
    node_id: NodeId
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address] = None
    state: Optional[NodeState] = None
    connection_uri: Optional[str] = None
    tags: Tags = Field(default_factory=dict)
    activity: Optional[Activity] = None

    class Config:
        arbitrary_types_allowed = True


class GetNodeRequestData(BaseModel):
    node_id: NodeId


class GetNodeResponseData(BaseModel):
    node: Node


class SingleNodeRequestData(BaseModel):
    node_id: NodeId


class NodeConfigData(BaseModel):
    image_url: Optional[str] = None  # FIXME: Use yarl.URL
    image_hash: Optional[str] = None
    image_tag: Optional[str] = None
    capabilities: List[str]
    min_mem_gib: float
    min_cpu_threads: int
    min_storage_gib: float


class CreateClusterRequestData(BaseModel):
    network: str
    budget: int
    num_workers: int = 4
    node_config: NodeConfigData


class CreateClusterResponseData(BaseModel):
    nodes: List[NodeId]


class NonTerminatedNodesRequestData(BaseModel):
    tags: Tags


class CreateNodesRequestData(BaseModel):
    count: int
    tags: Tags


class DeleteNodesRequestData(BaseModel):
    node_ids: List[NodeId]


class SetNodeTagsRequestData(BaseModel):
    node_id: NodeId
    tags: Tags


class CreateNodesResponseData(BaseModel):
    nodes: Dict[NodeId, Node]


class GetNodesResponseData(BaseModel):
    nodes: List[NodeId]


class IsRunningResponseData(BaseModel):
    is_running: bool


class IsTerminatedResponseData(BaseModel):
    is_terminated: bool


class GetNodeTagsResponseData(BaseModel):
    tags: Tags


class GetNodeIpAddressResponseData(BaseModel):
    ip_address: IPv4Address


class EmptyRequestData(BaseModel):
    pass


class EmptyResponseData(BaseModel):
    pass


class GetNodePortResponseData(BaseModel):
    port: int


class GetSshProxyCommandResponseData(BaseModel):
    ssh_proxy_command: str


class GetImageUrlFromHashRequestData(BaseModel):
    image_hash: str


class GetImageUrlFromHashResponseData(BaseModel):
    url: str


class GetImageUrlAndHashFromTagRequestData(BaseModel):
    image_tag: str


class GetImageUrlAndHashFromTagResponseData(BaseModel):
    url: str
    image_hash: str
