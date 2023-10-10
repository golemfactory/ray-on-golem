from src.ray.protobuf import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TablePrefix(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    TABLE_PREFIX_MIN: _ClassVar[TablePrefix]
    UNUSED: _ClassVar[TablePrefix]
    TASK: _ClassVar[TablePrefix]
    RAYLET_TASK: _ClassVar[TablePrefix]
    NODE: _ClassVar[TablePrefix]
    OBJECT: _ClassVar[TablePrefix]
    ACTOR: _ClassVar[TablePrefix]
    FUNCTION: _ClassVar[TablePrefix]
    TASK_RECONSTRUCTION: _ClassVar[TablePrefix]
    RESOURCE_USAGE_BATCH: _ClassVar[TablePrefix]
    JOB: _ClassVar[TablePrefix]
    TASK_LEASE: _ClassVar[TablePrefix]
    NODE_RESOURCE: _ClassVar[TablePrefix]
    DIRECT_ACTOR: _ClassVar[TablePrefix]
    WORKERS: _ClassVar[TablePrefix]
    INTERNAL_CONFIG: _ClassVar[TablePrefix]
    PLACEMENT_GROUP_SCHEDULE: _ClassVar[TablePrefix]
    PLACEMENT_GROUP: _ClassVar[TablePrefix]
    KV: _ClassVar[TablePrefix]
    ACTOR_TASK_SPEC: _ClassVar[TablePrefix]

class TablePubsub(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    TABLE_PUBSUB_MIN: _ClassVar[TablePubsub]
    NO_PUBLISH: _ClassVar[TablePubsub]
    TASK_PUBSUB: _ClassVar[TablePubsub]
    RAYLET_TASK_PUBSUB: _ClassVar[TablePubsub]
    NODE_PUBSUB: _ClassVar[TablePubsub]
    OBJECT_PUBSUB: _ClassVar[TablePubsub]
    ACTOR_PUBSUB: _ClassVar[TablePubsub]
    RESOURCE_USAGE_BATCH_PUBSUB: _ClassVar[TablePubsub]
    TASK_LEASE_PUBSUB: _ClassVar[TablePubsub]
    JOB_PUBSUB: _ClassVar[TablePubsub]
    NODE_RESOURCE_PUBSUB: _ClassVar[TablePubsub]
    DIRECT_ACTOR_PUBSUB: _ClassVar[TablePubsub]
    WORKER_FAILURE_PUBSUB: _ClassVar[TablePubsub]
    TABLE_PUBSUB_MAX: _ClassVar[TablePubsub]

class GcsChangeMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    APPEND_OR_ADD: _ClassVar[GcsChangeMode]
    REMOVE: _ClassVar[GcsChangeMode]
TABLE_PREFIX_MIN: TablePrefix
UNUSED: TablePrefix
TASK: TablePrefix
RAYLET_TASK: TablePrefix
NODE: TablePrefix
OBJECT: TablePrefix
ACTOR: TablePrefix
FUNCTION: TablePrefix
TASK_RECONSTRUCTION: TablePrefix
RESOURCE_USAGE_BATCH: TablePrefix
JOB: TablePrefix
TASK_LEASE: TablePrefix
NODE_RESOURCE: TablePrefix
DIRECT_ACTOR: TablePrefix
WORKERS: TablePrefix
INTERNAL_CONFIG: TablePrefix
PLACEMENT_GROUP_SCHEDULE: TablePrefix
PLACEMENT_GROUP: TablePrefix
KV: TablePrefix
ACTOR_TASK_SPEC: TablePrefix
TABLE_PUBSUB_MIN: TablePubsub
NO_PUBLISH: TablePubsub
TASK_PUBSUB: TablePubsub
RAYLET_TASK_PUBSUB: TablePubsub
NODE_PUBSUB: TablePubsub
OBJECT_PUBSUB: TablePubsub
ACTOR_PUBSUB: TablePubsub
RESOURCE_USAGE_BATCH_PUBSUB: TablePubsub
TASK_LEASE_PUBSUB: TablePubsub
JOB_PUBSUB: TablePubsub
NODE_RESOURCE_PUBSUB: TablePubsub
DIRECT_ACTOR_PUBSUB: TablePubsub
WORKER_FAILURE_PUBSUB: TablePubsub
TABLE_PUBSUB_MAX: TablePubsub
APPEND_OR_ADD: GcsChangeMode
REMOVE: GcsChangeMode

class GcsEntry(_message.Message):
    __slots__ = ["change_mode", "id", "entries"]
    CHANGE_MODE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    change_mode: GcsChangeMode
    id: bytes
    entries: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, change_mode: _Optional[_Union[GcsChangeMode, str]] = ..., id: _Optional[bytes] = ..., entries: _Optional[_Iterable[bytes]] = ...) -> None: ...

class ObjectTableData(_message.Message):
    __slots__ = ["manager"]
    MANAGER_FIELD_NUMBER: _ClassVar[int]
    manager: bytes
    def __init__(self, manager: _Optional[bytes] = ...) -> None: ...

class ActorTableData(_message.Message):
    __slots__ = ["actor_id", "parent_id", "actor_creation_dummy_object_id", "job_id", "state", "max_restarts", "num_restarts", "address", "owner_address", "is_detached", "name", "timestamp", "resource_mapping", "pid", "function_descriptor", "ray_namespace", "start_time", "end_time", "serialized_runtime_env", "class_name", "death_cause", "required_resources", "node_id", "placement_group_id", "repr_name"]
    class ActorState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        DEPENDENCIES_UNREADY: _ClassVar[ActorTableData.ActorState]
        PENDING_CREATION: _ClassVar[ActorTableData.ActorState]
        ALIVE: _ClassVar[ActorTableData.ActorState]
        RESTARTING: _ClassVar[ActorTableData.ActorState]
        DEAD: _ClassVar[ActorTableData.ActorState]
    DEPENDENCIES_UNREADY: ActorTableData.ActorState
    PENDING_CREATION: ActorTableData.ActorState
    ALIVE: ActorTableData.ActorState
    RESTARTING: ActorTableData.ActorState
    DEAD: ActorTableData.ActorState
    class RequiredResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_CREATION_DUMMY_OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    MAX_RESTARTS_FIELD_NUMBER: _ClassVar[int]
    NUM_RESTARTS_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OWNER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    IS_DETACHED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_MAPPING_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    SERIALIZED_RUNTIME_ENV_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    DEATH_CAUSE_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    REPR_NAME_FIELD_NUMBER: _ClassVar[int]
    actor_id: bytes
    parent_id: bytes
    actor_creation_dummy_object_id: bytes
    job_id: bytes
    state: ActorTableData.ActorState
    max_restarts: int
    num_restarts: int
    address: _common_pb2.Address
    owner_address: _common_pb2.Address
    is_detached: bool
    name: str
    timestamp: float
    resource_mapping: _containers.RepeatedCompositeFieldContainer[_common_pb2.ResourceMapEntry]
    pid: int
    function_descriptor: _common_pb2.FunctionDescriptor
    ray_namespace: str
    start_time: int
    end_time: int
    serialized_runtime_env: str
    class_name: str
    death_cause: _common_pb2.ActorDeathCause
    required_resources: _containers.ScalarMap[str, float]
    node_id: bytes
    placement_group_id: bytes
    repr_name: str
    def __init__(self, actor_id: _Optional[bytes] = ..., parent_id: _Optional[bytes] = ..., actor_creation_dummy_object_id: _Optional[bytes] = ..., job_id: _Optional[bytes] = ..., state: _Optional[_Union[ActorTableData.ActorState, str]] = ..., max_restarts: _Optional[int] = ..., num_restarts: _Optional[int] = ..., address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ..., owner_address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ..., is_detached: bool = ..., name: _Optional[str] = ..., timestamp: _Optional[float] = ..., resource_mapping: _Optional[_Iterable[_Union[_common_pb2.ResourceMapEntry, _Mapping]]] = ..., pid: _Optional[int] = ..., function_descriptor: _Optional[_Union[_common_pb2.FunctionDescriptor, _Mapping]] = ..., ray_namespace: _Optional[str] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., serialized_runtime_env: _Optional[str] = ..., class_name: _Optional[str] = ..., death_cause: _Optional[_Union[_common_pb2.ActorDeathCause, _Mapping]] = ..., required_resources: _Optional[_Mapping[str, float]] = ..., node_id: _Optional[bytes] = ..., placement_group_id: _Optional[bytes] = ..., repr_name: _Optional[str] = ...) -> None: ...

class ErrorTableData(_message.Message):
    __slots__ = ["job_id", "type", "error_message", "timestamp"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    job_id: bytes
    type: str
    error_message: str
    timestamp: float
    def __init__(self, job_id: _Optional[bytes] = ..., type: _Optional[str] = ..., error_message: _Optional[str] = ..., timestamp: _Optional[float] = ...) -> None: ...

class ScheduleData(_message.Message):
    __slots__ = ["schedule_plan"]
    class SchedulePlanEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    SCHEDULE_PLAN_FIELD_NUMBER: _ClassVar[int]
    schedule_plan: _containers.ScalarMap[str, bytes]
    def __init__(self, schedule_plan: _Optional[_Mapping[str, bytes]] = ...) -> None: ...

class ProfileEventEntry(_message.Message):
    __slots__ = ["start_time", "end_time", "extra_data", "event_name"]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    EXTRA_DATA_FIELD_NUMBER: _ClassVar[int]
    EVENT_NAME_FIELD_NUMBER: _ClassVar[int]
    start_time: int
    end_time: int
    extra_data: str
    event_name: str
    def __init__(self, start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., extra_data: _Optional[str] = ..., event_name: _Optional[str] = ...) -> None: ...

class ProfileEvents(_message.Message):
    __slots__ = ["component_type", "component_id", "node_ip_address", "events"]
    COMPONENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    component_type: str
    component_id: bytes
    node_ip_address: str
    events: _containers.RepeatedCompositeFieldContainer[ProfileEventEntry]
    def __init__(self, component_type: _Optional[str] = ..., component_id: _Optional[bytes] = ..., node_ip_address: _Optional[str] = ..., events: _Optional[_Iterable[_Union[ProfileEventEntry, _Mapping]]] = ...) -> None: ...

class TaskLogInfo(_message.Message):
    __slots__ = ["stdout_file", "stderr_file", "stdout_start", "stdout_end", "stderr_start", "stderr_end"]
    STDOUT_FILE_FIELD_NUMBER: _ClassVar[int]
    STDERR_FILE_FIELD_NUMBER: _ClassVar[int]
    STDOUT_START_FIELD_NUMBER: _ClassVar[int]
    STDOUT_END_FIELD_NUMBER: _ClassVar[int]
    STDERR_START_FIELD_NUMBER: _ClassVar[int]
    STDERR_END_FIELD_NUMBER: _ClassVar[int]
    stdout_file: str
    stderr_file: str
    stdout_start: int
    stdout_end: int
    stderr_start: int
    stderr_end: int
    def __init__(self, stdout_file: _Optional[str] = ..., stderr_file: _Optional[str] = ..., stdout_start: _Optional[int] = ..., stdout_end: _Optional[int] = ..., stderr_start: _Optional[int] = ..., stderr_end: _Optional[int] = ...) -> None: ...

class TaskStateUpdate(_message.Message):
    __slots__ = ["node_id", "pending_args_avail_ts", "pending_node_assignment_ts", "submitted_to_worker_ts", "running_ts", "finished_ts", "failed_ts", "worker_id", "error_info", "task_log_info", "actor_repr_name", "worker_pid"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PENDING_ARGS_AVAIL_TS_FIELD_NUMBER: _ClassVar[int]
    PENDING_NODE_ASSIGNMENT_TS_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_TO_WORKER_TS_FIELD_NUMBER: _ClassVar[int]
    RUNNING_TS_FIELD_NUMBER: _ClassVar[int]
    FINISHED_TS_FIELD_NUMBER: _ClassVar[int]
    FAILED_TS_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_INFO_FIELD_NUMBER: _ClassVar[int]
    TASK_LOG_INFO_FIELD_NUMBER: _ClassVar[int]
    ACTOR_REPR_NAME_FIELD_NUMBER: _ClassVar[int]
    WORKER_PID_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    pending_args_avail_ts: int
    pending_node_assignment_ts: int
    submitted_to_worker_ts: int
    running_ts: int
    finished_ts: int
    failed_ts: int
    worker_id: bytes
    error_info: _common_pb2.RayErrorInfo
    task_log_info: TaskLogInfo
    actor_repr_name: str
    worker_pid: int
    def __init__(self, node_id: _Optional[bytes] = ..., pending_args_avail_ts: _Optional[int] = ..., pending_node_assignment_ts: _Optional[int] = ..., submitted_to_worker_ts: _Optional[int] = ..., running_ts: _Optional[int] = ..., finished_ts: _Optional[int] = ..., failed_ts: _Optional[int] = ..., worker_id: _Optional[bytes] = ..., error_info: _Optional[_Union[_common_pb2.RayErrorInfo, _Mapping]] = ..., task_log_info: _Optional[_Union[TaskLogInfo, _Mapping]] = ..., actor_repr_name: _Optional[str] = ..., worker_pid: _Optional[int] = ...) -> None: ...

class TaskEvents(_message.Message):
    __slots__ = ["task_id", "attempt_number", "task_info", "state_updates", "profile_events", "job_id"]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TASK_INFO_FIELD_NUMBER: _ClassVar[int]
    STATE_UPDATES_FIELD_NUMBER: _ClassVar[int]
    PROFILE_EVENTS_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    task_id: bytes
    attempt_number: int
    task_info: _common_pb2.TaskInfoEntry
    state_updates: TaskStateUpdate
    profile_events: ProfileEvents
    job_id: bytes
    def __init__(self, task_id: _Optional[bytes] = ..., attempt_number: _Optional[int] = ..., task_info: _Optional[_Union[_common_pb2.TaskInfoEntry, _Mapping]] = ..., state_updates: _Optional[_Union[TaskStateUpdate, _Mapping]] = ..., profile_events: _Optional[_Union[ProfileEvents, _Mapping]] = ..., job_id: _Optional[bytes] = ...) -> None: ...

class TaskEventData(_message.Message):
    __slots__ = ["events_by_task", "num_profile_task_events_dropped", "num_status_task_events_dropped"]
    EVENTS_BY_TASK_FIELD_NUMBER: _ClassVar[int]
    NUM_PROFILE_TASK_EVENTS_DROPPED_FIELD_NUMBER: _ClassVar[int]
    NUM_STATUS_TASK_EVENTS_DROPPED_FIELD_NUMBER: _ClassVar[int]
    events_by_task: _containers.RepeatedCompositeFieldContainer[TaskEvents]
    num_profile_task_events_dropped: int
    num_status_task_events_dropped: int
    def __init__(self, events_by_task: _Optional[_Iterable[_Union[TaskEvents, _Mapping]]] = ..., num_profile_task_events_dropped: _Optional[int] = ..., num_status_task_events_dropped: _Optional[int] = ...) -> None: ...

class ResourceTableData(_message.Message):
    __slots__ = ["resource_capacity"]
    RESOURCE_CAPACITY_FIELD_NUMBER: _ClassVar[int]
    resource_capacity: float
    def __init__(self, resource_capacity: _Optional[float] = ...) -> None: ...

class AvailableResources(_message.Message):
    __slots__ = ["node_id", "resources_available"]
    class ResourcesAvailableEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    resources_available: _containers.ScalarMap[str, float]
    def __init__(self, node_id: _Optional[bytes] = ..., resources_available: _Optional[_Mapping[str, float]] = ...) -> None: ...

class NodeSnapshot(_message.Message):
    __slots__ = ["state", "idle_duration_ms", "node_activity"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        UNDEFINED: _ClassVar[NodeSnapshot.State]
        IDLE: _ClassVar[NodeSnapshot.State]
        ACTIVE: _ClassVar[NodeSnapshot.State]
        DRAINING: _ClassVar[NodeSnapshot.State]
    UNDEFINED: NodeSnapshot.State
    IDLE: NodeSnapshot.State
    ACTIVE: NodeSnapshot.State
    DRAINING: NodeSnapshot.State
    STATE_FIELD_NUMBER: _ClassVar[int]
    IDLE_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    NODE_ACTIVITY_FIELD_NUMBER: _ClassVar[int]
    state: NodeSnapshot.State
    idle_duration_ms: int
    node_activity: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, state: _Optional[_Union[NodeSnapshot.State, str]] = ..., idle_duration_ms: _Optional[int] = ..., node_activity: _Optional[_Iterable[str]] = ...) -> None: ...

class GcsNodeInfo(_message.Message):
    __slots__ = ["node_id", "node_manager_address", "raylet_socket_name", "object_store_socket_name", "node_manager_port", "object_manager_port", "state", "node_manager_hostname", "metrics_export_port", "runtime_env_agent_port", "resources_total", "node_name", "instance_id", "node_type_name", "instance_type_name", "start_time_ms", "end_time_ms", "is_head_node", "labels", "state_snapshot"]
    class GcsNodeState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        ALIVE: _ClassVar[GcsNodeInfo.GcsNodeState]
        DEAD: _ClassVar[GcsNodeInfo.GcsNodeState]
    ALIVE: GcsNodeInfo.GcsNodeState
    DEAD: GcsNodeInfo.GcsNodeState
    class ResourcesTotalEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class LabelsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_MANAGER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    RAYLET_SOCKET_NAME_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORE_SOCKET_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_MANAGER_PORT_FIELD_NUMBER: _ClassVar[int]
    OBJECT_MANAGER_PORT_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    NODE_MANAGER_HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    METRICS_EXPORT_PORT_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_AGENT_PORT_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_TOTAL_FIELD_NUMBER: _ClassVar[int]
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    END_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    IS_HEAD_NODE_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    STATE_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    node_manager_address: str
    raylet_socket_name: str
    object_store_socket_name: str
    node_manager_port: int
    object_manager_port: int
    state: GcsNodeInfo.GcsNodeState
    node_manager_hostname: str
    metrics_export_port: int
    runtime_env_agent_port: int
    resources_total: _containers.ScalarMap[str, float]
    node_name: str
    instance_id: str
    node_type_name: str
    instance_type_name: str
    start_time_ms: int
    end_time_ms: int
    is_head_node: bool
    labels: _containers.ScalarMap[str, str]
    state_snapshot: NodeSnapshot
    def __init__(self, node_id: _Optional[bytes] = ..., node_manager_address: _Optional[str] = ..., raylet_socket_name: _Optional[str] = ..., object_store_socket_name: _Optional[str] = ..., node_manager_port: _Optional[int] = ..., object_manager_port: _Optional[int] = ..., state: _Optional[_Union[GcsNodeInfo.GcsNodeState, str]] = ..., node_manager_hostname: _Optional[str] = ..., metrics_export_port: _Optional[int] = ..., runtime_env_agent_port: _Optional[int] = ..., resources_total: _Optional[_Mapping[str, float]] = ..., node_name: _Optional[str] = ..., instance_id: _Optional[str] = ..., node_type_name: _Optional[str] = ..., instance_type_name: _Optional[str] = ..., start_time_ms: _Optional[int] = ..., end_time_ms: _Optional[int] = ..., is_head_node: bool = ..., labels: _Optional[_Mapping[str, str]] = ..., state_snapshot: _Optional[_Union[NodeSnapshot, _Mapping]] = ...) -> None: ...

class JobsAPIInfo(_message.Message):
    __slots__ = ["status", "entrypoint", "message", "error_type", "start_time", "end_time", "metadata", "runtime_env_json", "entrypoint_num_cpus", "entrypoint_num_gpus", "entrypoint_resources", "driver_agent_http_address", "driver_node_id", "driver_exit_code", "entrypoint_memory"]
    class MetadataEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class EntrypointResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_JSON_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_NUM_CPUS_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_NUM_GPUS_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    DRIVER_AGENT_HTTP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    DRIVER_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    DRIVER_EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_MEMORY_FIELD_NUMBER: _ClassVar[int]
    status: str
    entrypoint: str
    message: str
    error_type: str
    start_time: int
    end_time: int
    metadata: _containers.ScalarMap[str, str]
    runtime_env_json: str
    entrypoint_num_cpus: float
    entrypoint_num_gpus: float
    entrypoint_resources: _containers.ScalarMap[str, float]
    driver_agent_http_address: str
    driver_node_id: str
    driver_exit_code: int
    entrypoint_memory: int
    def __init__(self, status: _Optional[str] = ..., entrypoint: _Optional[str] = ..., message: _Optional[str] = ..., error_type: _Optional[str] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., metadata: _Optional[_Mapping[str, str]] = ..., runtime_env_json: _Optional[str] = ..., entrypoint_num_cpus: _Optional[float] = ..., entrypoint_num_gpus: _Optional[float] = ..., entrypoint_resources: _Optional[_Mapping[str, float]] = ..., driver_agent_http_address: _Optional[str] = ..., driver_node_id: _Optional[str] = ..., driver_exit_code: _Optional[int] = ..., entrypoint_memory: _Optional[int] = ...) -> None: ...

class WorkerTableData(_message.Message):
    __slots__ = ["is_alive", "worker_address", "timestamp", "worker_type", "worker_info", "creation_task_exception", "exit_type", "exit_detail", "pid", "start_time_ms", "end_time_ms", "worker_launch_time_ms", "worker_launched_time_ms"]
    class WorkerInfoEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    IS_ALIVE_FIELD_NUMBER: _ClassVar[int]
    WORKER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    WORKER_TYPE_FIELD_NUMBER: _ClassVar[int]
    WORKER_INFO_FIELD_NUMBER: _ClassVar[int]
    CREATION_TASK_EXCEPTION_FIELD_NUMBER: _ClassVar[int]
    EXIT_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXIT_DETAIL_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    START_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    END_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    WORKER_LAUNCH_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    WORKER_LAUNCHED_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    is_alive: bool
    worker_address: _common_pb2.Address
    timestamp: int
    worker_type: _common_pb2.WorkerType
    worker_info: _containers.ScalarMap[str, bytes]
    creation_task_exception: _common_pb2.RayException
    exit_type: _common_pb2.WorkerExitType
    exit_detail: str
    pid: int
    start_time_ms: int
    end_time_ms: int
    worker_launch_time_ms: int
    worker_launched_time_ms: int
    def __init__(self, is_alive: bool = ..., worker_address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ..., timestamp: _Optional[int] = ..., worker_type: _Optional[_Union[_common_pb2.WorkerType, str]] = ..., worker_info: _Optional[_Mapping[str, bytes]] = ..., creation_task_exception: _Optional[_Union[_common_pb2.RayException, _Mapping]] = ..., exit_type: _Optional[_Union[_common_pb2.WorkerExitType, str]] = ..., exit_detail: _Optional[str] = ..., pid: _Optional[int] = ..., start_time_ms: _Optional[int] = ..., end_time_ms: _Optional[int] = ..., worker_launch_time_ms: _Optional[int] = ..., worker_launched_time_ms: _Optional[int] = ...) -> None: ...

class WorkerDeltaData(_message.Message):
    __slots__ = ["raylet_id", "worker_id"]
    RAYLET_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    raylet_id: bytes
    worker_id: bytes
    def __init__(self, raylet_id: _Optional[bytes] = ..., worker_id: _Optional[bytes] = ...) -> None: ...

class ResourceMap(_message.Message):
    __slots__ = ["items"]
    class ItemsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ResourceTableData
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ResourceTableData, _Mapping]] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.MessageMap[str, ResourceTableData]
    def __init__(self, items: _Optional[_Mapping[str, ResourceTableData]] = ...) -> None: ...

class StoredConfig(_message.Message):
    __slots__ = ["config"]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: str
    def __init__(self, config: _Optional[str] = ...) -> None: ...

class NodeResourceChange(_message.Message):
    __slots__ = ["node_id", "updated_resources", "deleted_resources"]
    class UpdatedResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    UPDATED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    DELETED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    updated_resources: _containers.ScalarMap[str, float]
    deleted_resources: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, node_id: _Optional[bytes] = ..., updated_resources: _Optional[_Mapping[str, float]] = ..., deleted_resources: _Optional[_Iterable[str]] = ...) -> None: ...

class PubSubMessage(_message.Message):
    __slots__ = ["id", "data"]
    ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    id: bytes
    data: bytes
    def __init__(self, id: _Optional[bytes] = ..., data: _Optional[bytes] = ...) -> None: ...

class ResourceUpdate(_message.Message):
    __slots__ = ["change", "data"]
    CHANGE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    change: NodeResourceChange
    data: ResourcesData
    def __init__(self, change: _Optional[_Union[NodeResourceChange, _Mapping]] = ..., data: _Optional[_Union[ResourcesData, _Mapping]] = ...) -> None: ...

class ResourceUsageBroadcastData(_message.Message):
    __slots__ = ["seq_no", "batch"]
    SEQ_NO_FIELD_NUMBER: _ClassVar[int]
    BATCH_FIELD_NUMBER: _ClassVar[int]
    seq_no: int
    batch: _containers.RepeatedCompositeFieldContainer[ResourceUpdate]
    def __init__(self, seq_no: _Optional[int] = ..., batch: _Optional[_Iterable[_Union[ResourceUpdate, _Mapping]]] = ...) -> None: ...

class ResourceDemand(_message.Message):
    __slots__ = ["shape", "num_ready_requests_queued", "num_infeasible_requests_queued", "backlog_size"]
    class ShapeEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    NUM_READY_REQUESTS_QUEUED_FIELD_NUMBER: _ClassVar[int]
    NUM_INFEASIBLE_REQUESTS_QUEUED_FIELD_NUMBER: _ClassVar[int]
    BACKLOG_SIZE_FIELD_NUMBER: _ClassVar[int]
    shape: _containers.ScalarMap[str, float]
    num_ready_requests_queued: int
    num_infeasible_requests_queued: int
    backlog_size: int
    def __init__(self, shape: _Optional[_Mapping[str, float]] = ..., num_ready_requests_queued: _Optional[int] = ..., num_infeasible_requests_queued: _Optional[int] = ..., backlog_size: _Optional[int] = ...) -> None: ...

class ResourceLoad(_message.Message):
    __slots__ = ["resource_demands"]
    RESOURCE_DEMANDS_FIELD_NUMBER: _ClassVar[int]
    resource_demands: _containers.RepeatedCompositeFieldContainer[ResourceDemand]
    def __init__(self, resource_demands: _Optional[_Iterable[_Union[ResourceDemand, _Mapping]]] = ...) -> None: ...

class ResourcesData(_message.Message):
    __slots__ = ["node_id", "resources_available", "resources_total", "resource_load", "resource_load_changed", "resource_load_by_shape", "should_global_gc", "node_manager_address", "object_pulls_queued", "resources_normal_task", "resources_normal_task_changed", "resources_normal_task_timestamp", "cluster_full_of_actors_detected", "idle_duration_ms", "is_draining", "node_activity"]
    class ResourcesAvailableEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class ResourcesTotalEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class ResourceLoadEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class ResourcesNormalTaskEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_TOTAL_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_LOAD_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_LOAD_CHANGED_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_LOAD_BY_SHAPE_FIELD_NUMBER: _ClassVar[int]
    SHOULD_GLOBAL_GC_FIELD_NUMBER: _ClassVar[int]
    NODE_MANAGER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OBJECT_PULLS_QUEUED_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_NORMAL_TASK_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_NORMAL_TASK_CHANGED_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_NORMAL_TASK_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_FULL_OF_ACTORS_DETECTED_FIELD_NUMBER: _ClassVar[int]
    IDLE_DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    IS_DRAINING_FIELD_NUMBER: _ClassVar[int]
    NODE_ACTIVITY_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    resources_available: _containers.ScalarMap[str, float]
    resources_total: _containers.ScalarMap[str, float]
    resource_load: _containers.ScalarMap[str, float]
    resource_load_changed: bool
    resource_load_by_shape: ResourceLoad
    should_global_gc: bool
    node_manager_address: str
    object_pulls_queued: bool
    resources_normal_task: _containers.ScalarMap[str, float]
    resources_normal_task_changed: bool
    resources_normal_task_timestamp: int
    cluster_full_of_actors_detected: bool
    idle_duration_ms: int
    is_draining: bool
    node_activity: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, node_id: _Optional[bytes] = ..., resources_available: _Optional[_Mapping[str, float]] = ..., resources_total: _Optional[_Mapping[str, float]] = ..., resource_load: _Optional[_Mapping[str, float]] = ..., resource_load_changed: bool = ..., resource_load_by_shape: _Optional[_Union[ResourceLoad, _Mapping]] = ..., should_global_gc: bool = ..., node_manager_address: _Optional[str] = ..., object_pulls_queued: bool = ..., resources_normal_task: _Optional[_Mapping[str, float]] = ..., resources_normal_task_changed: bool = ..., resources_normal_task_timestamp: _Optional[int] = ..., cluster_full_of_actors_detected: bool = ..., idle_duration_ms: _Optional[int] = ..., is_draining: bool = ..., node_activity: _Optional[_Iterable[str]] = ...) -> None: ...

class ResourceUsageBatchData(_message.Message):
    __slots__ = ["batch", "resource_load_by_shape", "placement_group_load"]
    BATCH_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_LOAD_BY_SHAPE_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_LOAD_FIELD_NUMBER: _ClassVar[int]
    batch: _containers.RepeatedCompositeFieldContainer[ResourcesData]
    resource_load_by_shape: ResourceLoad
    placement_group_load: PlacementGroupLoad
    def __init__(self, batch: _Optional[_Iterable[_Union[ResourcesData, _Mapping]]] = ..., resource_load_by_shape: _Optional[_Union[ResourceLoad, _Mapping]] = ..., placement_group_load: _Optional[_Union[PlacementGroupLoad, _Mapping]] = ...) -> None: ...

class PlacementGroupLoad(_message.Message):
    __slots__ = ["placement_group_data"]
    PLACEMENT_GROUP_DATA_FIELD_NUMBER: _ClassVar[int]
    placement_group_data: _containers.RepeatedCompositeFieldContainer[PlacementGroupTableData]
    def __init__(self, placement_group_data: _Optional[_Iterable[_Union[PlacementGroupTableData, _Mapping]]] = ...) -> None: ...

class PlacementGroupStats(_message.Message):
    __slots__ = ["creation_request_received_ns", "scheduling_started_time_ns", "scheduling_latency_us", "end_to_end_creation_latency_us", "scheduling_attempt", "highest_retry_delay_ms", "scheduling_state"]
    class SchedulingState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        QUEUED: _ClassVar[PlacementGroupStats.SchedulingState]
        REMOVED: _ClassVar[PlacementGroupStats.SchedulingState]
        SCHEDULING_STARTED: _ClassVar[PlacementGroupStats.SchedulingState]
        NO_RESOURCES: _ClassVar[PlacementGroupStats.SchedulingState]
        INFEASIBLE: _ClassVar[PlacementGroupStats.SchedulingState]
        FAILED_TO_COMMIT_RESOURCES: _ClassVar[PlacementGroupStats.SchedulingState]
        FINISHED: _ClassVar[PlacementGroupStats.SchedulingState]
    QUEUED: PlacementGroupStats.SchedulingState
    REMOVED: PlacementGroupStats.SchedulingState
    SCHEDULING_STARTED: PlacementGroupStats.SchedulingState
    NO_RESOURCES: PlacementGroupStats.SchedulingState
    INFEASIBLE: PlacementGroupStats.SchedulingState
    FAILED_TO_COMMIT_RESOURCES: PlacementGroupStats.SchedulingState
    FINISHED: PlacementGroupStats.SchedulingState
    CREATION_REQUEST_RECEIVED_NS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_STARTED_TIME_NS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_LATENCY_US_FIELD_NUMBER: _ClassVar[int]
    END_TO_END_CREATION_LATENCY_US_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_ATTEMPT_FIELD_NUMBER: _ClassVar[int]
    HIGHEST_RETRY_DELAY_MS_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_STATE_FIELD_NUMBER: _ClassVar[int]
    creation_request_received_ns: int
    scheduling_started_time_ns: int
    scheduling_latency_us: int
    end_to_end_creation_latency_us: int
    scheduling_attempt: int
    highest_retry_delay_ms: float
    scheduling_state: PlacementGroupStats.SchedulingState
    def __init__(self, creation_request_received_ns: _Optional[int] = ..., scheduling_started_time_ns: _Optional[int] = ..., scheduling_latency_us: _Optional[int] = ..., end_to_end_creation_latency_us: _Optional[int] = ..., scheduling_attempt: _Optional[int] = ..., highest_retry_delay_ms: _Optional[float] = ..., scheduling_state: _Optional[_Union[PlacementGroupStats.SchedulingState, str]] = ...) -> None: ...

class PlacementGroupTableData(_message.Message):
    __slots__ = ["placement_group_id", "name", "bundles", "strategy", "state", "creator_job_id", "creator_actor_id", "creator_job_dead", "creator_actor_dead", "is_detached", "ray_namespace", "stats", "max_cpu_fraction_per_node", "placement_group_creation_timestamp_ms", "placement_group_final_bundle_placement_timestamp_ms"]
    class PlacementGroupState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        PENDING: _ClassVar[PlacementGroupTableData.PlacementGroupState]
        CREATED: _ClassVar[PlacementGroupTableData.PlacementGroupState]
        REMOVED: _ClassVar[PlacementGroupTableData.PlacementGroupState]
        RESCHEDULING: _ClassVar[PlacementGroupTableData.PlacementGroupState]
    PENDING: PlacementGroupTableData.PlacementGroupState
    CREATED: PlacementGroupTableData.PlacementGroupState
    REMOVED: PlacementGroupTableData.PlacementGroupState
    RESCHEDULING: PlacementGroupTableData.PlacementGroupState
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BUNDLES_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    CREATOR_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    CREATOR_ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    CREATOR_JOB_DEAD_FIELD_NUMBER: _ClassVar[int]
    CREATOR_ACTOR_DEAD_FIELD_NUMBER: _ClassVar[int]
    IS_DETACHED_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    MAX_CPU_FRACTION_PER_NODE_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_CREATION_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_FINAL_BUNDLE_PLACEMENT_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    name: str
    bundles: _containers.RepeatedCompositeFieldContainer[_common_pb2.Bundle]
    strategy: _common_pb2.PlacementStrategy
    state: PlacementGroupTableData.PlacementGroupState
    creator_job_id: bytes
    creator_actor_id: bytes
    creator_job_dead: bool
    creator_actor_dead: bool
    is_detached: bool
    ray_namespace: str
    stats: PlacementGroupStats
    max_cpu_fraction_per_node: float
    placement_group_creation_timestamp_ms: int
    placement_group_final_bundle_placement_timestamp_ms: int
    def __init__(self, placement_group_id: _Optional[bytes] = ..., name: _Optional[str] = ..., bundles: _Optional[_Iterable[_Union[_common_pb2.Bundle, _Mapping]]] = ..., strategy: _Optional[_Union[_common_pb2.PlacementStrategy, str]] = ..., state: _Optional[_Union[PlacementGroupTableData.PlacementGroupState, str]] = ..., creator_job_id: _Optional[bytes] = ..., creator_actor_id: _Optional[bytes] = ..., creator_job_dead: bool = ..., creator_actor_dead: bool = ..., is_detached: bool = ..., ray_namespace: _Optional[str] = ..., stats: _Optional[_Union[PlacementGroupStats, _Mapping]] = ..., max_cpu_fraction_per_node: _Optional[float] = ..., placement_group_creation_timestamp_ms: _Optional[int] = ..., placement_group_final_bundle_placement_timestamp_ms: _Optional[int] = ...) -> None: ...

class JobTableData(_message.Message):
    __slots__ = ["job_id", "is_dead", "timestamp", "driver_ip_address", "driver_pid", "config", "start_time", "end_time", "entrypoint", "job_info", "is_running_tasks", "driver_address"]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    IS_DEAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DRIVER_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    DRIVER_PID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    ENTRYPOINT_FIELD_NUMBER: _ClassVar[int]
    JOB_INFO_FIELD_NUMBER: _ClassVar[int]
    IS_RUNNING_TASKS_FIELD_NUMBER: _ClassVar[int]
    DRIVER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    job_id: bytes
    is_dead: bool
    timestamp: int
    driver_ip_address: str
    driver_pid: int
    config: _common_pb2.JobConfig
    start_time: int
    end_time: int
    entrypoint: str
    job_info: JobsAPIInfo
    is_running_tasks: bool
    driver_address: _common_pb2.Address
    def __init__(self, job_id: _Optional[bytes] = ..., is_dead: bool = ..., timestamp: _Optional[int] = ..., driver_ip_address: _Optional[str] = ..., driver_pid: _Optional[int] = ..., config: _Optional[_Union[_common_pb2.JobConfig, _Mapping]] = ..., start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., entrypoint: _Optional[str] = ..., job_info: _Optional[_Union[JobsAPIInfo, _Mapping]] = ..., is_running_tasks: bool = ..., driver_address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ...) -> None: ...
