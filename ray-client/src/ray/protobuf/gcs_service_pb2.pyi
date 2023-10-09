from src.ray.protobuf import common_pb2 as _common_pb2
from src.ray.protobuf import gcs_pb2 as _gcs_pb2
from src.ray.protobuf import pubsub_pb2 as _pubsub_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GcsServiceFailureType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    RPC_DISCONNECT: _ClassVar[GcsServiceFailureType]
    GCS_SERVER_RESTART: _ClassVar[GcsServiceFailureType]
RPC_DISCONNECT: GcsServiceFailureType
GCS_SERVER_RESTART: GcsServiceFailureType

class AddJobRequest(_message.Message):
    __slots__ = ["data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _gcs_pb2.JobTableData
    def __init__(self, data: _Optional[_Union[_gcs_pb2.JobTableData, _Mapping]] = ...) -> None: ...

class AddJobReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class MarkJobFinishedRequest(_message.Message):
    __slots__ = ["job_id"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: bytes
    def __init__(self, job_id: _Optional[bytes] = ...) -> None: ...

class MarkJobFinishedReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetAllJobInfoRequest(_message.Message):
    __slots__ = ["limit"]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    limit: int
    def __init__(self, limit: _Optional[int] = ...) -> None: ...

class GetAllJobInfoReply(_message.Message):
    __slots__ = ["status", "job_info_list"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_INFO_LIST_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    job_info_list: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.JobTableData]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., job_info_list: _Optional[_Iterable[_Union[_gcs_pb2.JobTableData, _Mapping]]] = ...) -> None: ...

class ReportJobErrorRequest(_message.Message):
    __slots__ = ["job_error"]
    JOB_ERROR_FIELD_NUMBER: _ClassVar[int]
    job_error: _gcs_pb2.ErrorTableData
    def __init__(self, job_error: _Optional[_Union[_gcs_pb2.ErrorTableData, _Mapping]] = ...) -> None: ...

class ReportJobErrorReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetNextJobIDRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetNextJobIDReply(_message.Message):
    __slots__ = ["status", "job_id"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    job_id: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., job_id: _Optional[int] = ...) -> None: ...

class GetActorInfoRequest(_message.Message):
    __slots__ = ["actor_id", "name"]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    actor_id: bytes
    name: str
    def __init__(self, actor_id: _Optional[bytes] = ..., name: _Optional[str] = ...) -> None: ...

class GetActorInfoReply(_message.Message):
    __slots__ = ["status", "actor_table_data"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    actor_table_data: _gcs_pb2.ActorTableData
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., actor_table_data: _Optional[_Union[_gcs_pb2.ActorTableData, _Mapping]] = ...) -> None: ...

class GetNamedActorInfoRequest(_message.Message):
    __slots__ = ["name", "ray_namespace"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    name: str
    ray_namespace: str
    def __init__(self, name: _Optional[str] = ..., ray_namespace: _Optional[str] = ...) -> None: ...

class GetNamedActorInfoReply(_message.Message):
    __slots__ = ["status", "actor_table_data", "task_spec"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    actor_table_data: _gcs_pb2.ActorTableData
    task_spec: _common_pb2.TaskSpec
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., actor_table_data: _Optional[_Union[_gcs_pb2.ActorTableData, _Mapping]] = ..., task_spec: _Optional[_Union[_common_pb2.TaskSpec, _Mapping]] = ...) -> None: ...

class ListNamedActorsRequest(_message.Message):
    __slots__ = ["all_namespaces", "ray_namespace"]
    ALL_NAMESPACES_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    all_namespaces: bool
    ray_namespace: str
    def __init__(self, all_namespaces: bool = ..., ray_namespace: _Optional[str] = ...) -> None: ...

class ListNamedActorsReply(_message.Message):
    __slots__ = ["status", "named_actors_list"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NAMED_ACTORS_LIST_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    named_actors_list: _containers.RepeatedCompositeFieldContainer[_common_pb2.NamedActorInfo]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., named_actors_list: _Optional[_Iterable[_Union[_common_pb2.NamedActorInfo, _Mapping]]] = ...) -> None: ...

class GetAllActorInfoRequest(_message.Message):
    __slots__ = ["show_dead_jobs", "limit", "filters"]
    class Filters(_message.Message):
        __slots__ = ["actor_id", "job_id", "state"]
        ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
        JOB_ID_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        actor_id: bytes
        job_id: bytes
        state: _gcs_pb2.ActorTableData.ActorState
        def __init__(self, actor_id: _Optional[bytes] = ..., job_id: _Optional[bytes] = ..., state: _Optional[_Union[_gcs_pb2.ActorTableData.ActorState, str]] = ...) -> None: ...
    SHOW_DEAD_JOBS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    show_dead_jobs: bool
    limit: int
    filters: GetAllActorInfoRequest.Filters
    def __init__(self, show_dead_jobs: bool = ..., limit: _Optional[int] = ..., filters: _Optional[_Union[GetAllActorInfoRequest.Filters, _Mapping]] = ...) -> None: ...

class GetAllActorInfoReply(_message.Message):
    __slots__ = ["status", "actor_table_data", "total", "num_filtered"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    NUM_FILTERED_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    actor_table_data: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.ActorTableData]
    total: int
    num_filtered: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., actor_table_data: _Optional[_Iterable[_Union[_gcs_pb2.ActorTableData, _Mapping]]] = ..., total: _Optional[int] = ..., num_filtered: _Optional[int] = ...) -> None: ...

class KillActorViaGcsRequest(_message.Message):
    __slots__ = ["actor_id", "force_kill", "no_restart"]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_KILL_FIELD_NUMBER: _ClassVar[int]
    NO_RESTART_FIELD_NUMBER: _ClassVar[int]
    actor_id: bytes
    force_kill: bool
    no_restart: bool
    def __init__(self, actor_id: _Optional[bytes] = ..., force_kill: bool = ..., no_restart: bool = ...) -> None: ...

class KillActorViaGcsReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetClusterIdRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetClusterIdReply(_message.Message):
    __slots__ = ["status", "cluster_id"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    cluster_id: bytes
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., cluster_id: _Optional[bytes] = ...) -> None: ...

class RegisterNodeRequest(_message.Message):
    __slots__ = ["node_info"]
    NODE_INFO_FIELD_NUMBER: _ClassVar[int]
    node_info: _gcs_pb2.GcsNodeInfo
    def __init__(self, node_info: _Optional[_Union[_gcs_pb2.GcsNodeInfo, _Mapping]] = ...) -> None: ...

class RegisterNodeReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetAllNodeInfoRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetAllNodeInfoReply(_message.Message):
    __slots__ = ["status", "node_info_list"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NODE_INFO_LIST_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    node_info_list: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.GcsNodeInfo]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., node_info_list: _Optional[_Iterable[_Union[_gcs_pb2.GcsNodeInfo, _Mapping]]] = ...) -> None: ...

class CheckAliveRequest(_message.Message):
    __slots__ = ["raylet_address"]
    RAYLET_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    raylet_address: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, raylet_address: _Optional[_Iterable[str]] = ...) -> None: ...

class CheckAliveReply(_message.Message):
    __slots__ = ["status", "ray_version", "raylet_alive"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RAY_VERSION_FIELD_NUMBER: _ClassVar[int]
    RAYLET_ALIVE_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    ray_version: str
    raylet_alive: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., ray_version: _Optional[str] = ..., raylet_alive: _Optional[_Iterable[bool]] = ...) -> None: ...

class GetInternalConfigRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetInternalConfigReply(_message.Message):
    __slots__ = ["status", "config"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    config: str
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., config: _Optional[str] = ...) -> None: ...

class GetResourcesRequest(_message.Message):
    __slots__ = ["node_id"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    def __init__(self, node_id: _Optional[bytes] = ...) -> None: ...

class GetResourcesReply(_message.Message):
    __slots__ = ["status", "resources"]
    class ResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _gcs_pb2.ResourceTableData
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_gcs_pb2.ResourceTableData, _Mapping]] = ...) -> None: ...
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    resources: _containers.MessageMap[str, _gcs_pb2.ResourceTableData]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., resources: _Optional[_Mapping[str, _gcs_pb2.ResourceTableData]] = ...) -> None: ...

class DeleteResourcesReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetAllAvailableResourcesRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetAllAvailableResourcesReply(_message.Message):
    __slots__ = ["status", "resources_list"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_LIST_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    resources_list: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.AvailableResources]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., resources_list: _Optional[_Iterable[_Union[_gcs_pb2.AvailableResources, _Mapping]]] = ...) -> None: ...

class ReportResourceUsageRequest(_message.Message):
    __slots__ = ["resources"]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    resources: _gcs_pb2.ResourcesData
    def __init__(self, resources: _Optional[_Union[_gcs_pb2.ResourcesData, _Mapping]] = ...) -> None: ...

class ReportResourceUsageReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class ReportWorkerFailureRequest(_message.Message):
    __slots__ = ["worker_failure"]
    WORKER_FAILURE_FIELD_NUMBER: _ClassVar[int]
    worker_failure: _gcs_pb2.WorkerTableData
    def __init__(self, worker_failure: _Optional[_Union[_gcs_pb2.WorkerTableData, _Mapping]] = ...) -> None: ...

class ReportWorkerFailureReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetWorkerInfoRequest(_message.Message):
    __slots__ = ["worker_id"]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    worker_id: bytes
    def __init__(self, worker_id: _Optional[bytes] = ...) -> None: ...

class GetWorkerInfoReply(_message.Message):
    __slots__ = ["status", "worker_table_data"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKER_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    worker_table_data: _gcs_pb2.WorkerTableData
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., worker_table_data: _Optional[_Union[_gcs_pb2.WorkerTableData, _Mapping]] = ...) -> None: ...

class GetAllWorkerInfoRequest(_message.Message):
    __slots__ = ["limit"]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    limit: int
    def __init__(self, limit: _Optional[int] = ...) -> None: ...

class GetAllWorkerInfoReply(_message.Message):
    __slots__ = ["status", "worker_table_data", "total"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    WORKER_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    worker_table_data: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.WorkerTableData]
    total: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., worker_table_data: _Optional[_Iterable[_Union[_gcs_pb2.WorkerTableData, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class AddWorkerInfoRequest(_message.Message):
    __slots__ = ["worker_data"]
    WORKER_DATA_FIELD_NUMBER: _ClassVar[int]
    worker_data: _gcs_pb2.WorkerTableData
    def __init__(self, worker_data: _Optional[_Union[_gcs_pb2.WorkerTableData, _Mapping]] = ...) -> None: ...

class AddWorkerInfoReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class CreateActorRequest(_message.Message):
    __slots__ = ["task_spec"]
    TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    task_spec: _common_pb2.TaskSpec
    def __init__(self, task_spec: _Optional[_Union[_common_pb2.TaskSpec, _Mapping]] = ...) -> None: ...

class CreateActorReply(_message.Message):
    __slots__ = ["status", "actor_address", "borrowed_refs", "death_cause"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    BORROWED_REFS_FIELD_NUMBER: _ClassVar[int]
    DEATH_CAUSE_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    actor_address: _common_pb2.Address
    borrowed_refs: _containers.RepeatedCompositeFieldContainer[_common_pb2.ObjectReferenceCount]
    death_cause: _common_pb2.ActorDeathCause
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., actor_address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ..., borrowed_refs: _Optional[_Iterable[_Union[_common_pb2.ObjectReferenceCount, _Mapping]]] = ..., death_cause: _Optional[_Union[_common_pb2.ActorDeathCause, _Mapping]] = ...) -> None: ...

class RegisterActorRequest(_message.Message):
    __slots__ = ["task_spec"]
    TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    task_spec: _common_pb2.TaskSpec
    def __init__(self, task_spec: _Optional[_Union[_common_pb2.TaskSpec, _Mapping]] = ...) -> None: ...

class RegisterActorReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class CreatePlacementGroupRequest(_message.Message):
    __slots__ = ["placement_group_spec"]
    PLACEMENT_GROUP_SPEC_FIELD_NUMBER: _ClassVar[int]
    placement_group_spec: _common_pb2.PlacementGroupSpec
    def __init__(self, placement_group_spec: _Optional[_Union[_common_pb2.PlacementGroupSpec, _Mapping]] = ...) -> None: ...

class CreatePlacementGroupReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class RemovePlacementGroupRequest(_message.Message):
    __slots__ = ["placement_group_id"]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    def __init__(self, placement_group_id: _Optional[bytes] = ...) -> None: ...

class RemovePlacementGroupReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetPlacementGroupRequest(_message.Message):
    __slots__ = ["placement_group_id"]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    def __init__(self, placement_group_id: _Optional[bytes] = ...) -> None: ...

class GetPlacementGroupReply(_message.Message):
    __slots__ = ["status", "placement_group_table_data"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    placement_group_table_data: _gcs_pb2.PlacementGroupTableData
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., placement_group_table_data: _Optional[_Union[_gcs_pb2.PlacementGroupTableData, _Mapping]] = ...) -> None: ...

class GetAllPlacementGroupRequest(_message.Message):
    __slots__ = ["limit"]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    limit: int
    def __init__(self, limit: _Optional[int] = ...) -> None: ...

class GetAllPlacementGroupReply(_message.Message):
    __slots__ = ["status", "placement_group_table_data", "total"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    placement_group_table_data: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.PlacementGroupTableData]
    total: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., placement_group_table_data: _Optional[_Iterable[_Union[_gcs_pb2.PlacementGroupTableData, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class WaitPlacementGroupUntilReadyRequest(_message.Message):
    __slots__ = ["placement_group_id"]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    def __init__(self, placement_group_id: _Optional[bytes] = ...) -> None: ...

class WaitPlacementGroupUntilReadyReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetNamedPlacementGroupRequest(_message.Message):
    __slots__ = ["name", "ray_namespace"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    name: str
    ray_namespace: str
    def __init__(self, name: _Optional[str] = ..., ray_namespace: _Optional[str] = ...) -> None: ...

class GetNamedPlacementGroupReply(_message.Message):
    __slots__ = ["status", "placement_group_table_data"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_TABLE_DATA_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    placement_group_table_data: _gcs_pb2.PlacementGroupTableData
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., placement_group_table_data: _Optional[_Union[_gcs_pb2.PlacementGroupTableData, _Mapping]] = ...) -> None: ...

class DrainNodeData(_message.Message):
    __slots__ = ["node_id"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    def __init__(self, node_id: _Optional[bytes] = ...) -> None: ...

class DrainNodeRequest(_message.Message):
    __slots__ = ["drain_node_data"]
    DRAIN_NODE_DATA_FIELD_NUMBER: _ClassVar[int]
    drain_node_data: _containers.RepeatedCompositeFieldContainer[DrainNodeData]
    def __init__(self, drain_node_data: _Optional[_Iterable[_Union[DrainNodeData, _Mapping]]] = ...) -> None: ...

class DrainNodeStatus(_message.Message):
    __slots__ = ["node_id"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    def __init__(self, node_id: _Optional[bytes] = ...) -> None: ...

class DrainNodeReply(_message.Message):
    __slots__ = ["status", "drain_node_status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DRAIN_NODE_STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    drain_node_status: _containers.RepeatedCompositeFieldContainer[DrainNodeStatus]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., drain_node_status: _Optional[_Iterable[_Union[DrainNodeStatus, _Mapping]]] = ...) -> None: ...

class InternalKVGetRequest(_message.Message):
    __slots__ = ["key", "namespace"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    namespace: bytes
    def __init__(self, key: _Optional[bytes] = ..., namespace: _Optional[bytes] = ...) -> None: ...

class InternalKVGetReply(_message.Message):
    __slots__ = ["status", "value"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    value: bytes
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., value: _Optional[bytes] = ...) -> None: ...

class InternalKVMultiGetRequest(_message.Message):
    __slots__ = ["keys", "namespace"]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[bytes]
    namespace: bytes
    def __init__(self, keys: _Optional[_Iterable[bytes]] = ..., namespace: _Optional[bytes] = ...) -> None: ...

class MapFieldEntry(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ...) -> None: ...

class InternalKVMultiGetReply(_message.Message):
    __slots__ = ["status", "results"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    results: _containers.RepeatedCompositeFieldContainer[MapFieldEntry]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., results: _Optional[_Iterable[_Union[MapFieldEntry, _Mapping]]] = ...) -> None: ...

class InternalKVPutRequest(_message.Message):
    __slots__ = ["key", "value", "overwrite", "namespace"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    OVERWRITE_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    value: bytes
    overwrite: bool
    namespace: bytes
    def __init__(self, key: _Optional[bytes] = ..., value: _Optional[bytes] = ..., overwrite: bool = ..., namespace: _Optional[bytes] = ...) -> None: ...

class InternalKVPutReply(_message.Message):
    __slots__ = ["status", "added_num"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ADDED_NUM_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    added_num: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., added_num: _Optional[int] = ...) -> None: ...

class InternalKVDelRequest(_message.Message):
    __slots__ = ["key", "namespace", "del_by_prefix"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    DEL_BY_PREFIX_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    namespace: bytes
    del_by_prefix: bool
    def __init__(self, key: _Optional[bytes] = ..., namespace: _Optional[bytes] = ..., del_by_prefix: bool = ...) -> None: ...

class InternalKVDelReply(_message.Message):
    __slots__ = ["status", "deleted_num"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DELETED_NUM_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    deleted_num: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., deleted_num: _Optional[int] = ...) -> None: ...

class InternalKVExistsRequest(_message.Message):
    __slots__ = ["key", "namespace"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    key: bytes
    namespace: bytes
    def __init__(self, key: _Optional[bytes] = ..., namespace: _Optional[bytes] = ...) -> None: ...

class InternalKVExistsReply(_message.Message):
    __slots__ = ["status", "exists"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    exists: bool
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., exists: bool = ...) -> None: ...

class InternalKVKeysRequest(_message.Message):
    __slots__ = ["prefix", "namespace"]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    prefix: bytes
    namespace: bytes
    def __init__(self, prefix: _Optional[bytes] = ..., namespace: _Optional[bytes] = ...) -> None: ...

class InternalKVKeysReply(_message.Message):
    __slots__ = ["status", "results"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    results: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., results: _Optional[_Iterable[bytes]] = ...) -> None: ...

class PinRuntimeEnvURIRequest(_message.Message):
    __slots__ = ["uri", "expiration_s"]
    URI_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_S_FIELD_NUMBER: _ClassVar[int]
    uri: str
    expiration_s: int
    def __init__(self, uri: _Optional[str] = ..., expiration_s: _Optional[int] = ...) -> None: ...

class PinRuntimeEnvURIReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GcsPublishRequest(_message.Message):
    __slots__ = ["pub_messages"]
    PUB_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    pub_messages: _containers.RepeatedCompositeFieldContainer[_pubsub_pb2.PubMessage]
    def __init__(self, pub_messages: _Optional[_Iterable[_Union[_pubsub_pb2.PubMessage, _Mapping]]] = ...) -> None: ...

class GcsPublishReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GcsSubscriberPollRequest(_message.Message):
    __slots__ = ["subscriber_id", "max_processed_sequence_id", "publisher_id"]
    SUBSCRIBER_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_PROCESSED_SEQUENCE_ID_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_ID_FIELD_NUMBER: _ClassVar[int]
    subscriber_id: bytes
    max_processed_sequence_id: int
    publisher_id: bytes
    def __init__(self, subscriber_id: _Optional[bytes] = ..., max_processed_sequence_id: _Optional[int] = ..., publisher_id: _Optional[bytes] = ...) -> None: ...

class GcsSubscriberPollReply(_message.Message):
    __slots__ = ["pub_messages", "publisher_id", "status"]
    PUB_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    pub_messages: _containers.RepeatedCompositeFieldContainer[_pubsub_pb2.PubMessage]
    publisher_id: bytes
    status: GcsStatus
    def __init__(self, pub_messages: _Optional[_Iterable[_Union[_pubsub_pb2.PubMessage, _Mapping]]] = ..., publisher_id: _Optional[bytes] = ..., status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GcsSubscriberCommandBatchRequest(_message.Message):
    __slots__ = ["subscriber_id", "commands", "sender_id"]
    SUBSCRIBER_ID_FIELD_NUMBER: _ClassVar[int]
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    subscriber_id: bytes
    commands: _containers.RepeatedCompositeFieldContainer[_pubsub_pb2.Command]
    sender_id: bytes
    def __init__(self, subscriber_id: _Optional[bytes] = ..., commands: _Optional[_Iterable[_Union[_pubsub_pb2.Command, _Mapping]]] = ..., sender_id: _Optional[bytes] = ...) -> None: ...

class GcsSubscriberCommandBatchReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetAllResourceUsageRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetAllResourceUsageReply(_message.Message):
    __slots__ = ["status", "resource_usage_data", "cluster_full_of_actors_detected_by_gcs"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_USAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_FULL_OF_ACTORS_DETECTED_BY_GCS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    resource_usage_data: _gcs_pb2.ResourceUsageBatchData
    cluster_full_of_actors_detected_by_gcs: bool
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., resource_usage_data: _Optional[_Union[_gcs_pb2.ResourceUsageBatchData, _Mapping]] = ..., cluster_full_of_actors_detected_by_gcs: bool = ...) -> None: ...

class GetDrainingNodesRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetDrainingNodesReply(_message.Message):
    __slots__ = ["status", "node_ids"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    node_ids: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., node_ids: _Optional[_Iterable[bytes]] = ...) -> None: ...

class GcsStatus(_message.Message):
    __slots__ = ["code", "message"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class AddTaskEventDataRequest(_message.Message):
    __slots__ = ["data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _gcs_pb2.TaskEventData
    def __init__(self, data: _Optional[_Union[_gcs_pb2.TaskEventData, _Mapping]] = ...) -> None: ...

class AddTaskEventDataReply(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ...) -> None: ...

class GetTaskEventsRequest(_message.Message):
    __slots__ = ["limit", "filters"]
    class Filters(_message.Message):
        __slots__ = ["job_id", "task_ids", "actor_id", "name", "exclude_driver"]
        JOB_ID_FIELD_NUMBER: _ClassVar[int]
        TASK_IDS_FIELD_NUMBER: _ClassVar[int]
        ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        EXCLUDE_DRIVER_FIELD_NUMBER: _ClassVar[int]
        job_id: bytes
        task_ids: _containers.RepeatedScalarFieldContainer[bytes]
        actor_id: bytes
        name: str
        exclude_driver: bool
        def __init__(self, job_id: _Optional[bytes] = ..., task_ids: _Optional[_Iterable[bytes]] = ..., actor_id: _Optional[bytes] = ..., name: _Optional[str] = ..., exclude_driver: bool = ...) -> None: ...
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    limit: int
    filters: GetTaskEventsRequest.Filters
    def __init__(self, limit: _Optional[int] = ..., filters: _Optional[_Union[GetTaskEventsRequest.Filters, _Mapping]] = ...) -> None: ...

class GetTaskEventsReply(_message.Message):
    __slots__ = ["status", "events_by_task", "num_profile_task_events_dropped", "num_status_task_events_dropped"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_BY_TASK_FIELD_NUMBER: _ClassVar[int]
    NUM_PROFILE_TASK_EVENTS_DROPPED_FIELD_NUMBER: _ClassVar[int]
    NUM_STATUS_TASK_EVENTS_DROPPED_FIELD_NUMBER: _ClassVar[int]
    status: GcsStatus
    events_by_task: _containers.RepeatedCompositeFieldContainer[_gcs_pb2.TaskEvents]
    num_profile_task_events_dropped: int
    num_status_task_events_dropped: int
    def __init__(self, status: _Optional[_Union[GcsStatus, _Mapping]] = ..., events_by_task: _Optional[_Iterable[_Union[_gcs_pb2.TaskEvents, _Mapping]]] = ..., num_profile_task_events_dropped: _Optional[int] = ..., num_status_task_events_dropped: _Optional[int] = ...) -> None: ...
