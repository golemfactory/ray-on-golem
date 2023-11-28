from enum import Enum
from typing import Any, Dict, List, Optional

from golem.resources import Activity
from pydantic import AnyUrl, BaseModel, Field, root_validator

NodeId = str
Tags = Dict[str, str]


class NodeState(Enum):
    pending = "pending"
    running = "running"
    terminating = "terminating"
    terminated = "terminated"


class ShutdownState(Enum):
    NOT_ENABLED = "not_enabled"
    CLUSTER_NOT_EMPTY = "cluster_not_empty"
    WILL_SHUTDOWN = "will_shutdown"


class NodeData(BaseModel):
    node_id: NodeId
    tags: Tags
    state: NodeState = NodeState.pending
    state_log: List[str] = []
    internal_ip: Optional[str] = None
    ssh_proxy_command: Optional[str] = None


class Node(NodeData):
    activity: Optional[Activity] = None

    class Config:
        arbitrary_types_allowed = True


class SingleNodeRequestData(BaseModel):
    node_id: NodeId


class GetClusterDataRequestData(BaseModel):
    pass


class GetClusterDataResponseData(BaseModel):
    cluster_data: Dict[NodeId, NodeData]


class DemandConfigData(BaseModel):
    image_hash: Optional[str] = None
    image_tag: Optional[str] = None
    capabilities: List[str] = ["vpn", "inet"]
    outbound_urls: List[AnyUrl] = []
    min_mem_gib: float = 0.0
    min_cpu_threads: int = 0
    min_storage_gib: float = 0.0


class BudgetControlData(BaseModel):
    expected_cpu_load: Optional[float] = None
    expected_duration_minutes: Optional[float] = None

    max_expected_usage_cost: Optional[float] = None
    max_initial_price: Optional[float] = None
    max_cpu_sec_price: Optional[float] = None
    max_duration_sec_price: Optional[float] = None

    @root_validator
    def check_expected_fields(cls, values):
        expected_cpu_load = values.get("expected_cpu_load")
        expected_duration_minutes = values.get("expected_duration_minutes")
        max_expected_usage_cost = values.get("max_expected_usage_cost")

        if expected_cpu_load is None != expected_duration_minutes is None:
            raise ValueError(
                "Both `expected_cpu_load` and `expected_duration_minutes` parameter should be "
                "defined together!"
            )

        if max_expected_usage_cost is not None and (
            expected_cpu_load is None or expected_duration_minutes is None
        ):
            raise ValueError(
                "Parameter `max_expected_usage_cost` requires `expected_cpu_load` "
                "and `expected_duration_minutes` parameters to be defined!"
            )

        return values

    def is_expected_usage_cost_enabled(self):
        return self.expected_cpu_load is not None and self.expected_duration_minutes is not None


class NodeConfigData(BaseModel):
    demand: DemandConfigData = Field(default_factory=DemandConfigData)
    budget_control: Optional[BudgetControlData] = None


class ProviderConfigData(BaseModel):
    network: str
    budget_limit: int
    node_config: NodeConfigData
    ssh_private_key: str
    ssh_user: str
    subnet_tag: Optional[str]


class CreateClusterRequestData(ProviderConfigData):
    pass


class NonTerminatedNodesRequestData(BaseModel):
    tags: Tags


class NonTerminatedNodesResponseData(BaseModel):
    nodes_ids: List[NodeId]


class RequestNodesRequestData(BaseModel):
    node_config: Dict[str, Any]
    count: int
    tags: Tags


class RequestNodesResponseData(BaseModel):
    requested_nodes: List[NodeId]


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
    ip_address: Optional[str]


class EmptyResponseData(BaseModel):
    pass


class GetSshProxyCommandResponseData(BaseModel):
    ssh_proxy_command: Optional[str]


class GetOrCreateDefaultSshKeyRequestData(BaseModel):
    cluster_name: str


class GetOrCreateDefaultSshKeyResponseData(BaseModel):
    ssh_key_base64: str


class SelfShutdownRequestData(BaseModel):
    pass


class SelfShutdownResponseData(BaseModel):
    shutdown_state: ShutdownState
