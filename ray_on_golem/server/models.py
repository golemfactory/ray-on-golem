from enum import Enum
from typing import Any, Dict, List, Optional

from golem_core.core.activity_api import Activity
from pydantic import BaseModel

NodeId = str
Tags = Dict[str, str]


class NodeState(Enum):
    pending = "pending"
    running = "running"
    stopping = "stopping"


class ShutdownState(Enum):
    NOT_ENABLED = "not_enabled"
    CLUSTER_NOT_EMPTY = "cluster_not_empty"
    WILL_SHUTDOWN = "will_shutdown"


class Node(BaseModel):
    node_id: NodeId
    state: NodeState
    tags: Tags
    internal_ip: str
    ssh_proxy_command: str
    activity: Activity

    class Config:
        arbitrary_types_allowed = True


class SingleNodeRequestData(BaseModel):
    node_id: NodeId


class NodeConfigData(BaseModel):
    image_hash: Optional[str] = None
    image_tag: Optional[str] = None
    capabilities: List[str]
    min_mem_gib: float
    min_cpu_threads: int
    min_storage_gib: float


class CreateClusterRequestData(BaseModel):
    network: str
    budget: int
    node_config: NodeConfigData
    ssh_private_key: str


class NonTerminatedNodesRequestData(BaseModel):
    tags: Tags


class NonTerminatedNodesResponseData(BaseModel):
    nodes_ids: List[NodeId]


class CreateNodesRequestData(BaseModel):
    node_config: Dict[str, Any]
    count: int
    tags: Tags


class CreateNodesResponseData(BaseModel):
    created_nodes: Dict[NodeId, Dict]


class SetNodeTagsRequestData(BaseModel):
    node_id: NodeId
    tags: Tags


class TerminateNodeResponseData(BaseModel):
    terminated_nodes: Dict[NodeId, Dict]


class IsRunningResponseData(BaseModel):
    is_running: bool


class IsTerminatedResponseData(BaseModel):
    is_terminated: bool


class GetNodeTagsResponseData(BaseModel):
    tags: Tags


class GetNodeIpAddressResponseData(BaseModel):
    ip_address: str


class EmptyResponseData(BaseModel):
    pass


class GetSshProxyCommandResponseData(BaseModel):
    ssh_proxy_command: str


class GetOrCreateDefaultSshKeyRequestData(BaseModel):
    cluster_name: str


class GetOrCreateDefaultSshKeyResponseData(BaseModel):
    ssh_key_base64: str


class SelfShutdownRequestData(BaseModel):
    pass


class SelfShutdownResponseData(BaseModel):
    shutdown_state: ShutdownState
