from enum import Enum
from typing import Any, Dict, List, Optional

from golem.resources import Activity
from pydantic import BaseModel, root_validator

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


class DemandConfigData(BaseModel):
    image_hash: Optional[str] = None
    image_tag: Optional[str] = None
    capabilities: List[str]
    min_mem_gib: float
    min_cpu_threads: int
    min_storage_gib: float


class CostManagementData(BaseModel):
    average_cpu_load: Optional[float] = None
    average_duration_minutes: Optional[float] = None

    max_average_usage_cost: Optional[float] = None
    max_initial_price: Optional[float] = None
    max_cpu_sec_price: Optional[float] = None
    max_duration_sec_price: Optional[float] = None

    @root_validator
    def check_average_fields(cls, values):
        average_cpu_load = values.get("average_cpu_load")
        average_duration_minutes = values.get("average_duration_minutes")
        max_average_usage_cost = values.get("max_average_usage_cost")

        if average_cpu_load is None != average_duration_minutes is None:
            raise ValueError(
                "Both `average_cpu_load` and `average_duration_minutes` parameter should be defined together!"
            )

        if max_average_usage_cost is not None and (
            average_cpu_load is None or average_duration_minutes is None
        ):
            raise ValueError(
                "Parameter `max_average_usage_cost` requires `average_cpu_load` and `average_duration_minutes`"
                " parameters to be defined!"
            )

        return values

    def is_average_usage_cost_enabled(self):
        return self.average_cpu_load is not None and self.average_duration_minutes is not None


class NodeConfigData(BaseModel):
    demand: DemandConfigData
    cost_management: Optional[CostManagementData] = None


class ProviderConfigData(BaseModel):
    network: str
    budget: int
    node_config: NodeConfigData
    ssh_private_key: str
    ssh_user: str


class CreateClusterRequestData(ProviderConfigData):
    pass


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
