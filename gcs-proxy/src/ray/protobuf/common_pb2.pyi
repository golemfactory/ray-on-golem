from src.ray.protobuf import runtime_env_common_pb2 as _runtime_env_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Language(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    PYTHON: _ClassVar[Language]
    JAVA: _ClassVar[Language]
    CPP: _ClassVar[Language]

class WorkerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    WORKER: _ClassVar[WorkerType]
    DRIVER: _ClassVar[WorkerType]
    SPILL_WORKER: _ClassVar[WorkerType]
    RESTORE_WORKER: _ClassVar[WorkerType]

class TaskType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    NORMAL_TASK: _ClassVar[TaskType]
    ACTOR_CREATION_TASK: _ClassVar[TaskType]
    ACTOR_TASK: _ClassVar[TaskType]
    DRIVER_TASK: _ClassVar[TaskType]

class ErrorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    WORKER_DIED: _ClassVar[ErrorType]
    ACTOR_DIED: _ClassVar[ErrorType]
    OBJECT_UNRECONSTRUCTABLE: _ClassVar[ErrorType]
    TASK_EXECUTION_EXCEPTION: _ClassVar[ErrorType]
    OBJECT_IN_PLASMA: _ClassVar[ErrorType]
    TASK_CANCELLED: _ClassVar[ErrorType]
    ACTOR_CREATION_FAILED: _ClassVar[ErrorType]
    RUNTIME_ENV_SETUP_FAILED: _ClassVar[ErrorType]
    OBJECT_LOST: _ClassVar[ErrorType]
    OWNER_DIED: _ClassVar[ErrorType]
    OBJECT_DELETED: _ClassVar[ErrorType]
    DEPENDENCY_RESOLUTION_FAILED: _ClassVar[ErrorType]
    OBJECT_UNRECONSTRUCTABLE_MAX_ATTEMPTS_EXCEEDED: _ClassVar[ErrorType]
    OBJECT_UNRECONSTRUCTABLE_LINEAGE_EVICTED: _ClassVar[ErrorType]
    OBJECT_FETCH_TIMED_OUT: _ClassVar[ErrorType]
    LOCAL_RAYLET_DIED: _ClassVar[ErrorType]
    TASK_PLACEMENT_GROUP_REMOVED: _ClassVar[ErrorType]
    ACTOR_PLACEMENT_GROUP_REMOVED: _ClassVar[ErrorType]
    TASK_UNSCHEDULABLE_ERROR: _ClassVar[ErrorType]
    ACTOR_UNSCHEDULABLE_ERROR: _ClassVar[ErrorType]
    OUT_OF_DISK_ERROR: _ClassVar[ErrorType]
    OBJECT_FREED: _ClassVar[ErrorType]
    OUT_OF_MEMORY: _ClassVar[ErrorType]
    NODE_DIED: _ClassVar[ErrorType]
    END_OF_STREAMING_GENERATOR: _ClassVar[ErrorType]

class TaskStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    NIL: _ClassVar[TaskStatus]
    PENDING_ARGS_AVAIL: _ClassVar[TaskStatus]
    PENDING_NODE_ASSIGNMENT: _ClassVar[TaskStatus]
    PENDING_OBJ_STORE_MEM_AVAIL: _ClassVar[TaskStatus]
    PENDING_ARGS_FETCH: _ClassVar[TaskStatus]
    SUBMITTED_TO_WORKER: _ClassVar[TaskStatus]
    RUNNING: _ClassVar[TaskStatus]
    RUNNING_IN_RAY_GET: _ClassVar[TaskStatus]
    RUNNING_IN_RAY_WAIT: _ClassVar[TaskStatus]
    FINISHED: _ClassVar[TaskStatus]
    FAILED: _ClassVar[TaskStatus]

class WorkerExitType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    SYSTEM_ERROR: _ClassVar[WorkerExitType]
    INTENDED_SYSTEM_EXIT: _ClassVar[WorkerExitType]
    USER_ERROR: _ClassVar[WorkerExitType]
    INTENDED_USER_EXIT: _ClassVar[WorkerExitType]
    NODE_OUT_OF_MEMORY: _ClassVar[WorkerExitType]

class PlacementStrategy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    PACK: _ClassVar[PlacementStrategy]
    SPREAD: _ClassVar[PlacementStrategy]
    STRICT_PACK: _ClassVar[PlacementStrategy]
    STRICT_SPREAD: _ClassVar[PlacementStrategy]
PYTHON: Language
JAVA: Language
CPP: Language
WORKER: WorkerType
DRIVER: WorkerType
SPILL_WORKER: WorkerType
RESTORE_WORKER: WorkerType
NORMAL_TASK: TaskType
ACTOR_CREATION_TASK: TaskType
ACTOR_TASK: TaskType
DRIVER_TASK: TaskType
WORKER_DIED: ErrorType
ACTOR_DIED: ErrorType
OBJECT_UNRECONSTRUCTABLE: ErrorType
TASK_EXECUTION_EXCEPTION: ErrorType
OBJECT_IN_PLASMA: ErrorType
TASK_CANCELLED: ErrorType
ACTOR_CREATION_FAILED: ErrorType
RUNTIME_ENV_SETUP_FAILED: ErrorType
OBJECT_LOST: ErrorType
OWNER_DIED: ErrorType
OBJECT_DELETED: ErrorType
DEPENDENCY_RESOLUTION_FAILED: ErrorType
OBJECT_UNRECONSTRUCTABLE_MAX_ATTEMPTS_EXCEEDED: ErrorType
OBJECT_UNRECONSTRUCTABLE_LINEAGE_EVICTED: ErrorType
OBJECT_FETCH_TIMED_OUT: ErrorType
LOCAL_RAYLET_DIED: ErrorType
TASK_PLACEMENT_GROUP_REMOVED: ErrorType
ACTOR_PLACEMENT_GROUP_REMOVED: ErrorType
TASK_UNSCHEDULABLE_ERROR: ErrorType
ACTOR_UNSCHEDULABLE_ERROR: ErrorType
OUT_OF_DISK_ERROR: ErrorType
OBJECT_FREED: ErrorType
OUT_OF_MEMORY: ErrorType
NODE_DIED: ErrorType
END_OF_STREAMING_GENERATOR: ErrorType
NIL: TaskStatus
PENDING_ARGS_AVAIL: TaskStatus
PENDING_NODE_ASSIGNMENT: TaskStatus
PENDING_OBJ_STORE_MEM_AVAIL: TaskStatus
PENDING_ARGS_FETCH: TaskStatus
SUBMITTED_TO_WORKER: TaskStatus
RUNNING: TaskStatus
RUNNING_IN_RAY_GET: TaskStatus
RUNNING_IN_RAY_WAIT: TaskStatus
FINISHED: TaskStatus
FAILED: TaskStatus
SYSTEM_ERROR: WorkerExitType
INTENDED_SYSTEM_EXIT: WorkerExitType
USER_ERROR: WorkerExitType
INTENDED_USER_EXIT: WorkerExitType
NODE_OUT_OF_MEMORY: WorkerExitType
PACK: PlacementStrategy
SPREAD: PlacementStrategy
STRICT_PACK: PlacementStrategy
STRICT_SPREAD: PlacementStrategy

class LabelIn(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class LabelNotIn(_message.Message):
    __slots__ = ["values"]
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class LabelExists(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LabelDoesNotExist(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LabelOperator(_message.Message):
    __slots__ = ["label_in", "label_not_in", "label_exists", "label_does_not_exist"]
    LABEL_IN_FIELD_NUMBER: _ClassVar[int]
    LABEL_NOT_IN_FIELD_NUMBER: _ClassVar[int]
    LABEL_EXISTS_FIELD_NUMBER: _ClassVar[int]
    LABEL_DOES_NOT_EXIST_FIELD_NUMBER: _ClassVar[int]
    label_in: LabelIn
    label_not_in: LabelNotIn
    label_exists: LabelExists
    label_does_not_exist: LabelDoesNotExist
    def __init__(self, label_in: _Optional[_Union[LabelIn, _Mapping]] = ..., label_not_in: _Optional[_Union[LabelNotIn, _Mapping]] = ..., label_exists: _Optional[_Union[LabelExists, _Mapping]] = ..., label_does_not_exist: _Optional[_Union[LabelDoesNotExist, _Mapping]] = ...) -> None: ...

class LabelMatchExpression(_message.Message):
    __slots__ = ["key", "operator"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_FIELD_NUMBER: _ClassVar[int]
    key: str
    operator: LabelOperator
    def __init__(self, key: _Optional[str] = ..., operator: _Optional[_Union[LabelOperator, _Mapping]] = ...) -> None: ...

class LabelMatchExpressions(_message.Message):
    __slots__ = ["expressions"]
    EXPRESSIONS_FIELD_NUMBER: _ClassVar[int]
    expressions: _containers.RepeatedCompositeFieldContainer[LabelMatchExpression]
    def __init__(self, expressions: _Optional[_Iterable[_Union[LabelMatchExpression, _Mapping]]] = ...) -> None: ...

class NodeLabelSchedulingStrategy(_message.Message):
    __slots__ = ["hard", "soft"]
    HARD_FIELD_NUMBER: _ClassVar[int]
    SOFT_FIELD_NUMBER: _ClassVar[int]
    hard: LabelMatchExpressions
    soft: LabelMatchExpressions
    def __init__(self, hard: _Optional[_Union[LabelMatchExpressions, _Mapping]] = ..., soft: _Optional[_Union[LabelMatchExpressions, _Mapping]] = ...) -> None: ...

class NodeAffinitySchedulingStrategy(_message.Message):
    __slots__ = ["node_id", "soft", "spill_on_unavailable", "fail_on_unavailable"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    SOFT_FIELD_NUMBER: _ClassVar[int]
    SPILL_ON_UNAVAILABLE_FIELD_NUMBER: _ClassVar[int]
    FAIL_ON_UNAVAILABLE_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    soft: bool
    spill_on_unavailable: bool
    fail_on_unavailable: bool
    def __init__(self, node_id: _Optional[bytes] = ..., soft: bool = ..., spill_on_unavailable: bool = ..., fail_on_unavailable: bool = ...) -> None: ...

class PlacementGroupSchedulingStrategy(_message.Message):
    __slots__ = ["placement_group_id", "placement_group_bundle_index", "placement_group_capture_child_tasks"]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_BUNDLE_INDEX_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_CAPTURE_CHILD_TASKS_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    placement_group_bundle_index: int
    placement_group_capture_child_tasks: bool
    def __init__(self, placement_group_id: _Optional[bytes] = ..., placement_group_bundle_index: _Optional[int] = ..., placement_group_capture_child_tasks: bool = ...) -> None: ...

class DefaultSchedulingStrategy(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SpreadSchedulingStrategy(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SchedulingStrategy(_message.Message):
    __slots__ = ["default_scheduling_strategy", "placement_group_scheduling_strategy", "spread_scheduling_strategy", "node_affinity_scheduling_strategy", "node_label_scheduling_strategy"]
    DEFAULT_SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    SPREAD_SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    NODE_AFFINITY_SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    NODE_LABEL_SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    default_scheduling_strategy: DefaultSchedulingStrategy
    placement_group_scheduling_strategy: PlacementGroupSchedulingStrategy
    spread_scheduling_strategy: SpreadSchedulingStrategy
    node_affinity_scheduling_strategy: NodeAffinitySchedulingStrategy
    node_label_scheduling_strategy: NodeLabelSchedulingStrategy
    def __init__(self, default_scheduling_strategy: _Optional[_Union[DefaultSchedulingStrategy, _Mapping]] = ..., placement_group_scheduling_strategy: _Optional[_Union[PlacementGroupSchedulingStrategy, _Mapping]] = ..., spread_scheduling_strategy: _Optional[_Union[SpreadSchedulingStrategy, _Mapping]] = ..., node_affinity_scheduling_strategy: _Optional[_Union[NodeAffinitySchedulingStrategy, _Mapping]] = ..., node_label_scheduling_strategy: _Optional[_Union[NodeLabelSchedulingStrategy, _Mapping]] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ["raylet_id", "ip_address", "port", "worker_id"]
    RAYLET_ID_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    raylet_id: bytes
    ip_address: str
    port: int
    worker_id: bytes
    def __init__(self, raylet_id: _Optional[bytes] = ..., ip_address: _Optional[str] = ..., port: _Optional[int] = ..., worker_id: _Optional[bytes] = ...) -> None: ...

class JavaFunctionDescriptor(_message.Message):
    __slots__ = ["class_name", "function_name", "signature"]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_NAME_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    class_name: str
    function_name: str
    signature: str
    def __init__(self, class_name: _Optional[str] = ..., function_name: _Optional[str] = ..., signature: _Optional[str] = ...) -> None: ...

class PythonFunctionDescriptor(_message.Message):
    __slots__ = ["module_name", "class_name", "function_name", "function_hash"]
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_NAME_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_HASH_FIELD_NUMBER: _ClassVar[int]
    module_name: str
    class_name: str
    function_name: str
    function_hash: str
    def __init__(self, module_name: _Optional[str] = ..., class_name: _Optional[str] = ..., function_name: _Optional[str] = ..., function_hash: _Optional[str] = ...) -> None: ...

class CppFunctionDescriptor(_message.Message):
    __slots__ = ["function_name", "caller", "class_name"]
    FUNCTION_NAME_FIELD_NUMBER: _ClassVar[int]
    CALLER_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    function_name: str
    caller: str
    class_name: str
    def __init__(self, function_name: _Optional[str] = ..., caller: _Optional[str] = ..., class_name: _Optional[str] = ...) -> None: ...

class FunctionDescriptor(_message.Message):
    __slots__ = ["java_function_descriptor", "python_function_descriptor", "cpp_function_descriptor"]
    JAVA_FUNCTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    PYTHON_FUNCTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    CPP_FUNCTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    java_function_descriptor: JavaFunctionDescriptor
    python_function_descriptor: PythonFunctionDescriptor
    cpp_function_descriptor: CppFunctionDescriptor
    def __init__(self, java_function_descriptor: _Optional[_Union[JavaFunctionDescriptor, _Mapping]] = ..., python_function_descriptor: _Optional[_Union[PythonFunctionDescriptor, _Mapping]] = ..., cpp_function_descriptor: _Optional[_Union[CppFunctionDescriptor, _Mapping]] = ...) -> None: ...

class ConcurrencyGroup(_message.Message):
    __slots__ = ["name", "max_concurrency", "function_descriptors"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MAX_CONCURRENCY_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DESCRIPTORS_FIELD_NUMBER: _ClassVar[int]
    name: str
    max_concurrency: int
    function_descriptors: _containers.RepeatedCompositeFieldContainer[FunctionDescriptor]
    def __init__(self, name: _Optional[str] = ..., max_concurrency: _Optional[int] = ..., function_descriptors: _Optional[_Iterable[_Union[FunctionDescriptor, _Mapping]]] = ...) -> None: ...

class RayErrorInfo(_message.Message):
    __slots__ = ["actor_died_error", "runtime_env_setup_failed_error", "error_message", "error_type"]
    ACTOR_DIED_ERROR_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_SETUP_FAILED_ERROR_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_TYPE_FIELD_NUMBER: _ClassVar[int]
    actor_died_error: ActorDeathCause
    runtime_env_setup_failed_error: RuntimeEnvFailedContext
    error_message: str
    error_type: ErrorType
    def __init__(self, actor_died_error: _Optional[_Union[ActorDeathCause, _Mapping]] = ..., runtime_env_setup_failed_error: _Optional[_Union[RuntimeEnvFailedContext, _Mapping]] = ..., error_message: _Optional[str] = ..., error_type: _Optional[_Union[ErrorType, str]] = ...) -> None: ...

class OutOfMemoryErrorContext(_message.Message):
    __slots__ = ["task_id", "task_name", "node_ip_address", "memory_used_bytes", "memory_total_bytes", "memory_usage_fraction", "memory_threshold"]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USED_BYTES_FIELD_NUMBER: _ClassVar[int]
    MEMORY_TOTAL_BYTES_FIELD_NUMBER: _ClassVar[int]
    MEMORY_USAGE_FRACTION_FIELD_NUMBER: _ClassVar[int]
    MEMORY_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    task_id: bytes
    task_name: str
    node_ip_address: str
    memory_used_bytes: int
    memory_total_bytes: int
    memory_usage_fraction: float
    memory_threshold: float
    def __init__(self, task_id: _Optional[bytes] = ..., task_name: _Optional[str] = ..., node_ip_address: _Optional[str] = ..., memory_used_bytes: _Optional[int] = ..., memory_total_bytes: _Optional[int] = ..., memory_usage_fraction: _Optional[float] = ..., memory_threshold: _Optional[float] = ...) -> None: ...

class NodeDiedErrorContext(_message.Message):
    __slots__ = ["node_id", "node_ip_address"]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    node_id: bytes
    node_ip_address: str
    def __init__(self, node_id: _Optional[bytes] = ..., node_ip_address: _Optional[str] = ...) -> None: ...

class RayException(_message.Message):
    __slots__ = ["language", "serialized_exception", "formatted_exception_string"]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    SERIALIZED_EXCEPTION_FIELD_NUMBER: _ClassVar[int]
    FORMATTED_EXCEPTION_STRING_FIELD_NUMBER: _ClassVar[int]
    language: Language
    serialized_exception: bytes
    formatted_exception_string: str
    def __init__(self, language: _Optional[_Union[Language, str]] = ..., serialized_exception: _Optional[bytes] = ..., formatted_exception_string: _Optional[str] = ...) -> None: ...

class ActorDeathCause(_message.Message):
    __slots__ = ["creation_task_failure_context", "runtime_env_failed_context", "actor_died_error_context", "actor_unschedulable_context", "oom_context"]
    CREATION_TASK_FAILURE_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_FAILED_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_DIED_ERROR_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_UNSCHEDULABLE_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    OOM_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    creation_task_failure_context: RayException
    runtime_env_failed_context: RuntimeEnvFailedContext
    actor_died_error_context: ActorDiedErrorContext
    actor_unschedulable_context: ActorUnschedulableContext
    oom_context: OomContext
    def __init__(self, creation_task_failure_context: _Optional[_Union[RayException, _Mapping]] = ..., runtime_env_failed_context: _Optional[_Union[RuntimeEnvFailedContext, _Mapping]] = ..., actor_died_error_context: _Optional[_Union[ActorDiedErrorContext, _Mapping]] = ..., actor_unschedulable_context: _Optional[_Union[ActorUnschedulableContext, _Mapping]] = ..., oom_context: _Optional[_Union[OomContext, _Mapping]] = ...) -> None: ...

class RuntimeEnvFailedContext(_message.Message):
    __slots__ = ["error_message"]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    def __init__(self, error_message: _Optional[str] = ...) -> None: ...

class ActorUnschedulableContext(_message.Message):
    __slots__ = ["error_message"]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    def __init__(self, error_message: _Optional[str] = ...) -> None: ...

class ActorDiedErrorContext(_message.Message):
    __slots__ = ["error_message", "owner_id", "owner_ip_address", "node_ip_address", "pid", "name", "ray_namespace", "class_name", "actor_id", "never_started"]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    OWNER_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    NODE_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    NEVER_STARTED_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    owner_id: bytes
    owner_ip_address: str
    node_ip_address: str
    pid: int
    name: str
    ray_namespace: str
    class_name: str
    actor_id: bytes
    never_started: bool
    def __init__(self, error_message: _Optional[str] = ..., owner_id: _Optional[bytes] = ..., owner_ip_address: _Optional[str] = ..., node_ip_address: _Optional[str] = ..., pid: _Optional[int] = ..., name: _Optional[str] = ..., ray_namespace: _Optional[str] = ..., class_name: _Optional[str] = ..., actor_id: _Optional[bytes] = ..., never_started: bool = ...) -> None: ...

class OomContext(_message.Message):
    __slots__ = ["error_message", "fail_immediately"]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FAIL_IMMEDIATELY_FIELD_NUMBER: _ClassVar[int]
    error_message: str
    fail_immediately: bool
    def __init__(self, error_message: _Optional[str] = ..., fail_immediately: bool = ...) -> None: ...

class JobConfig(_message.Message):
    __slots__ = ["jvm_options", "code_search_path", "runtime_env_info", "ray_namespace", "metadata", "default_actor_lifetime", "py_driver_sys_path"]
    class ActorLifetime(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
        DETACHED: _ClassVar[JobConfig.ActorLifetime]
        NON_DETACHED: _ClassVar[JobConfig.ActorLifetime]
    DETACHED: JobConfig.ActorLifetime
    NON_DETACHED: JobConfig.ActorLifetime
    class MetadataEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    JVM_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    CODE_SEARCH_PATH_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_INFO_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ACTOR_LIFETIME_FIELD_NUMBER: _ClassVar[int]
    PY_DRIVER_SYS_PATH_FIELD_NUMBER: _ClassVar[int]
    jvm_options: _containers.RepeatedScalarFieldContainer[str]
    code_search_path: _containers.RepeatedScalarFieldContainer[str]
    runtime_env_info: _runtime_env_common_pb2.RuntimeEnvInfo
    ray_namespace: str
    metadata: _containers.ScalarMap[str, str]
    default_actor_lifetime: JobConfig.ActorLifetime
    py_driver_sys_path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, jvm_options: _Optional[_Iterable[str]] = ..., code_search_path: _Optional[_Iterable[str]] = ..., runtime_env_info: _Optional[_Union[_runtime_env_common_pb2.RuntimeEnvInfo, _Mapping]] = ..., ray_namespace: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ..., default_actor_lifetime: _Optional[_Union[JobConfig.ActorLifetime, str]] = ..., py_driver_sys_path: _Optional[_Iterable[str]] = ...) -> None: ...

class StreamingGeneratorReturnIdInfo(_message.Message):
    __slots__ = ["object_id", "is_plasma_object"]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    IS_PLASMA_OBJECT_FIELD_NUMBER: _ClassVar[int]
    object_id: bytes
    is_plasma_object: bool
    def __init__(self, object_id: _Optional[bytes] = ..., is_plasma_object: bool = ...) -> None: ...

class TaskSpec(_message.Message):
    __slots__ = ["type", "name", "language", "function_descriptor", "job_id", "task_id", "parent_task_id", "parent_counter", "caller_id", "caller_address", "args", "num_returns", "required_resources", "required_placement_resources", "actor_creation_task_spec", "actor_task_spec", "max_retries", "skip_execution", "debugger_breakpoint", "runtime_env_info", "concurrency_group_name", "retry_exceptions", "serialized_retry_exception_allowlist", "depth", "scheduling_strategy", "attempt_number", "returns_dynamic", "dynamic_return_ids", "job_config", "submitter_task_id", "streaming_generator", "dependency_resolution_timestamp_ms", "lease_grant_timestamp_ms", "num_streaming_generator_returns"]
    class RequiredResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class RequiredPlacementResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_COUNTER_FIELD_NUMBER: _ClassVar[int]
    CALLER_ID_FIELD_NUMBER: _ClassVar[int]
    CALLER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    NUM_RETURNS_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_PLACEMENT_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    ACTOR_CREATION_TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    MAX_RETRIES_FIELD_NUMBER: _ClassVar[int]
    SKIP_EXECUTION_FIELD_NUMBER: _ClassVar[int]
    DEBUGGER_BREAKPOINT_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_INFO_FIELD_NUMBER: _ClassVar[int]
    CONCURRENCY_GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    RETRY_EXCEPTIONS_FIELD_NUMBER: _ClassVar[int]
    SERIALIZED_RETRY_EXCEPTION_ALLOWLIST_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_STRATEGY_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RETURNS_DYNAMIC_FIELD_NUMBER: _ClassVar[int]
    DYNAMIC_RETURN_IDS_FIELD_NUMBER: _ClassVar[int]
    JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SUBMITTER_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    STREAMING_GENERATOR_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCY_RESOLUTION_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    LEASE_GRANT_TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    NUM_STREAMING_GENERATOR_RETURNS_FIELD_NUMBER: _ClassVar[int]
    type: TaskType
    name: str
    language: Language
    function_descriptor: FunctionDescriptor
    job_id: bytes
    task_id: bytes
    parent_task_id: bytes
    parent_counter: int
    caller_id: bytes
    caller_address: Address
    args: _containers.RepeatedCompositeFieldContainer[TaskArg]
    num_returns: int
    required_resources: _containers.ScalarMap[str, float]
    required_placement_resources: _containers.ScalarMap[str, float]
    actor_creation_task_spec: ActorCreationTaskSpec
    actor_task_spec: ActorTaskSpec
    max_retries: int
    skip_execution: bool
    debugger_breakpoint: bytes
    runtime_env_info: _runtime_env_common_pb2.RuntimeEnvInfo
    concurrency_group_name: str
    retry_exceptions: bool
    serialized_retry_exception_allowlist: bytes
    depth: int
    scheduling_strategy: SchedulingStrategy
    attempt_number: int
    returns_dynamic: bool
    dynamic_return_ids: _containers.RepeatedScalarFieldContainer[bytes]
    job_config: JobConfig
    submitter_task_id: bytes
    streaming_generator: bool
    dependency_resolution_timestamp_ms: int
    lease_grant_timestamp_ms: int
    num_streaming_generator_returns: int
    def __init__(self, type: _Optional[_Union[TaskType, str]] = ..., name: _Optional[str] = ..., language: _Optional[_Union[Language, str]] = ..., function_descriptor: _Optional[_Union[FunctionDescriptor, _Mapping]] = ..., job_id: _Optional[bytes] = ..., task_id: _Optional[bytes] = ..., parent_task_id: _Optional[bytes] = ..., parent_counter: _Optional[int] = ..., caller_id: _Optional[bytes] = ..., caller_address: _Optional[_Union[Address, _Mapping]] = ..., args: _Optional[_Iterable[_Union[TaskArg, _Mapping]]] = ..., num_returns: _Optional[int] = ..., required_resources: _Optional[_Mapping[str, float]] = ..., required_placement_resources: _Optional[_Mapping[str, float]] = ..., actor_creation_task_spec: _Optional[_Union[ActorCreationTaskSpec, _Mapping]] = ..., actor_task_spec: _Optional[_Union[ActorTaskSpec, _Mapping]] = ..., max_retries: _Optional[int] = ..., skip_execution: bool = ..., debugger_breakpoint: _Optional[bytes] = ..., runtime_env_info: _Optional[_Union[_runtime_env_common_pb2.RuntimeEnvInfo, _Mapping]] = ..., concurrency_group_name: _Optional[str] = ..., retry_exceptions: bool = ..., serialized_retry_exception_allowlist: _Optional[bytes] = ..., depth: _Optional[int] = ..., scheduling_strategy: _Optional[_Union[SchedulingStrategy, _Mapping]] = ..., attempt_number: _Optional[int] = ..., returns_dynamic: bool = ..., dynamic_return_ids: _Optional[_Iterable[bytes]] = ..., job_config: _Optional[_Union[JobConfig, _Mapping]] = ..., submitter_task_id: _Optional[bytes] = ..., streaming_generator: bool = ..., dependency_resolution_timestamp_ms: _Optional[int] = ..., lease_grant_timestamp_ms: _Optional[int] = ..., num_streaming_generator_returns: _Optional[int] = ...) -> None: ...

class TaskInfoEntry(_message.Message):
    __slots__ = ["type", "name", "language", "func_or_class_name", "scheduling_state", "job_id", "task_id", "parent_task_id", "required_resources", "runtime_env_info", "node_id", "actor_id", "placement_group_id"]
    class RequiredResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    FUNC_OR_CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    SCHEDULING_STATE_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_INFO_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    type: TaskType
    name: str
    language: Language
    func_or_class_name: str
    scheduling_state: TaskStatus
    job_id: bytes
    task_id: bytes
    parent_task_id: bytes
    required_resources: _containers.ScalarMap[str, float]
    runtime_env_info: _runtime_env_common_pb2.RuntimeEnvInfo
    node_id: bytes
    actor_id: bytes
    placement_group_id: bytes
    def __init__(self, type: _Optional[_Union[TaskType, str]] = ..., name: _Optional[str] = ..., language: _Optional[_Union[Language, str]] = ..., func_or_class_name: _Optional[str] = ..., scheduling_state: _Optional[_Union[TaskStatus, str]] = ..., job_id: _Optional[bytes] = ..., task_id: _Optional[bytes] = ..., parent_task_id: _Optional[bytes] = ..., required_resources: _Optional[_Mapping[str, float]] = ..., runtime_env_info: _Optional[_Union[_runtime_env_common_pb2.RuntimeEnvInfo, _Mapping]] = ..., node_id: _Optional[bytes] = ..., actor_id: _Optional[bytes] = ..., placement_group_id: _Optional[bytes] = ...) -> None: ...

class Bundle(_message.Message):
    __slots__ = ["bundle_id", "unit_resources", "node_id"]
    class BundleIdentifier(_message.Message):
        __slots__ = ["placement_group_id", "bundle_index"]
        PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        BUNDLE_INDEX_FIELD_NUMBER: _ClassVar[int]
        placement_group_id: bytes
        bundle_index: int
        def __init__(self, placement_group_id: _Optional[bytes] = ..., bundle_index: _Optional[int] = ...) -> None: ...
    class UnitResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    BUNDLE_ID_FIELD_NUMBER: _ClassVar[int]
    UNIT_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    bundle_id: Bundle.BundleIdentifier
    unit_resources: _containers.ScalarMap[str, float]
    node_id: bytes
    def __init__(self, bundle_id: _Optional[_Union[Bundle.BundleIdentifier, _Mapping]] = ..., unit_resources: _Optional[_Mapping[str, float]] = ..., node_id: _Optional[bytes] = ...) -> None: ...

class PlacementGroupSpec(_message.Message):
    __slots__ = ["placement_group_id", "name", "bundles", "strategy", "creator_job_id", "creator_actor_id", "creator_job_dead", "creator_actor_dead", "is_detached", "max_cpu_fraction_per_node"]
    PLACEMENT_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BUNDLES_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    CREATOR_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    CREATOR_ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    CREATOR_JOB_DEAD_FIELD_NUMBER: _ClassVar[int]
    CREATOR_ACTOR_DEAD_FIELD_NUMBER: _ClassVar[int]
    IS_DETACHED_FIELD_NUMBER: _ClassVar[int]
    MAX_CPU_FRACTION_PER_NODE_FIELD_NUMBER: _ClassVar[int]
    placement_group_id: bytes
    name: str
    bundles: _containers.RepeatedCompositeFieldContainer[Bundle]
    strategy: PlacementStrategy
    creator_job_id: bytes
    creator_actor_id: bytes
    creator_job_dead: bool
    creator_actor_dead: bool
    is_detached: bool
    max_cpu_fraction_per_node: float
    def __init__(self, placement_group_id: _Optional[bytes] = ..., name: _Optional[str] = ..., bundles: _Optional[_Iterable[_Union[Bundle, _Mapping]]] = ..., strategy: _Optional[_Union[PlacementStrategy, str]] = ..., creator_job_id: _Optional[bytes] = ..., creator_actor_id: _Optional[bytes] = ..., creator_job_dead: bool = ..., creator_actor_dead: bool = ..., is_detached: bool = ..., max_cpu_fraction_per_node: _Optional[float] = ...) -> None: ...

class ObjectReference(_message.Message):
    __slots__ = ["object_id", "owner_address", "call_site"]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    OWNER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CALL_SITE_FIELD_NUMBER: _ClassVar[int]
    object_id: bytes
    owner_address: Address
    call_site: str
    def __init__(self, object_id: _Optional[bytes] = ..., owner_address: _Optional[_Union[Address, _Mapping]] = ..., call_site: _Optional[str] = ...) -> None: ...

class ObjectReferenceCount(_message.Message):
    __slots__ = ["reference", "has_local_ref", "borrowers", "stored_in_objects", "contained_in_borrowed_ids", "contains"]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    HAS_LOCAL_REF_FIELD_NUMBER: _ClassVar[int]
    BORROWERS_FIELD_NUMBER: _ClassVar[int]
    STORED_IN_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    CONTAINED_IN_BORROWED_IDS_FIELD_NUMBER: _ClassVar[int]
    CONTAINS_FIELD_NUMBER: _ClassVar[int]
    reference: ObjectReference
    has_local_ref: bool
    borrowers: _containers.RepeatedCompositeFieldContainer[Address]
    stored_in_objects: _containers.RepeatedCompositeFieldContainer[ObjectReference]
    contained_in_borrowed_ids: _containers.RepeatedScalarFieldContainer[bytes]
    contains: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, reference: _Optional[_Union[ObjectReference, _Mapping]] = ..., has_local_ref: bool = ..., borrowers: _Optional[_Iterable[_Union[Address, _Mapping]]] = ..., stored_in_objects: _Optional[_Iterable[_Union[ObjectReference, _Mapping]]] = ..., contained_in_borrowed_ids: _Optional[_Iterable[bytes]] = ..., contains: _Optional[_Iterable[bytes]] = ...) -> None: ...

class TaskArg(_message.Message):
    __slots__ = ["object_ref", "data", "metadata", "nested_inlined_refs"]
    OBJECT_REF_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NESTED_INLINED_REFS_FIELD_NUMBER: _ClassVar[int]
    object_ref: ObjectReference
    data: bytes
    metadata: bytes
    nested_inlined_refs: _containers.RepeatedCompositeFieldContainer[ObjectReference]
    def __init__(self, object_ref: _Optional[_Union[ObjectReference, _Mapping]] = ..., data: _Optional[bytes] = ..., metadata: _Optional[bytes] = ..., nested_inlined_refs: _Optional[_Iterable[_Union[ObjectReference, _Mapping]]] = ...) -> None: ...

class ReturnObject(_message.Message):
    __slots__ = ["object_id", "in_plasma", "data", "metadata", "nested_inlined_refs", "size"]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    IN_PLASMA_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NESTED_INLINED_REFS_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    object_id: bytes
    in_plasma: bool
    data: bytes
    metadata: bytes
    nested_inlined_refs: _containers.RepeatedCompositeFieldContainer[ObjectReference]
    size: int
    def __init__(self, object_id: _Optional[bytes] = ..., in_plasma: bool = ..., data: _Optional[bytes] = ..., metadata: _Optional[bytes] = ..., nested_inlined_refs: _Optional[_Iterable[_Union[ObjectReference, _Mapping]]] = ..., size: _Optional[int] = ...) -> None: ...

class ActorCreationTaskSpec(_message.Message):
    __slots__ = ["actor_id", "max_actor_restarts", "max_task_retries", "dynamic_worker_options", "max_concurrency", "is_detached", "name", "ray_namespace", "is_asyncio", "extension_data", "serialized_actor_handle", "concurrency_groups", "execute_out_of_order", "max_pending_calls"]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_ACTOR_RESTARTS_FIELD_NUMBER: _ClassVar[int]
    MAX_TASK_RETRIES_FIELD_NUMBER: _ClassVar[int]
    DYNAMIC_WORKER_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_CONCURRENCY_FIELD_NUMBER: _ClassVar[int]
    IS_DETACHED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    IS_ASYNCIO_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_DATA_FIELD_NUMBER: _ClassVar[int]
    SERIALIZED_ACTOR_HANDLE_FIELD_NUMBER: _ClassVar[int]
    CONCURRENCY_GROUPS_FIELD_NUMBER: _ClassVar[int]
    EXECUTE_OUT_OF_ORDER_FIELD_NUMBER: _ClassVar[int]
    MAX_PENDING_CALLS_FIELD_NUMBER: _ClassVar[int]
    actor_id: bytes
    max_actor_restarts: int
    max_task_retries: int
    dynamic_worker_options: _containers.RepeatedScalarFieldContainer[str]
    max_concurrency: int
    is_detached: bool
    name: str
    ray_namespace: str
    is_asyncio: bool
    extension_data: str
    serialized_actor_handle: bytes
    concurrency_groups: _containers.RepeatedCompositeFieldContainer[ConcurrencyGroup]
    execute_out_of_order: bool
    max_pending_calls: int
    def __init__(self, actor_id: _Optional[bytes] = ..., max_actor_restarts: _Optional[int] = ..., max_task_retries: _Optional[int] = ..., dynamic_worker_options: _Optional[_Iterable[str]] = ..., max_concurrency: _Optional[int] = ..., is_detached: bool = ..., name: _Optional[str] = ..., ray_namespace: _Optional[str] = ..., is_asyncio: bool = ..., extension_data: _Optional[str] = ..., serialized_actor_handle: _Optional[bytes] = ..., concurrency_groups: _Optional[_Iterable[_Union[ConcurrencyGroup, _Mapping]]] = ..., execute_out_of_order: bool = ..., max_pending_calls: _Optional[int] = ...) -> None: ...

class ActorTaskSpec(_message.Message):
    __slots__ = ["actor_id", "actor_creation_dummy_object_id", "actor_counter"]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_CREATION_DUMMY_OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_COUNTER_FIELD_NUMBER: _ClassVar[int]
    actor_id: bytes
    actor_creation_dummy_object_id: bytes
    actor_counter: int
    def __init__(self, actor_id: _Optional[bytes] = ..., actor_creation_dummy_object_id: _Optional[bytes] = ..., actor_counter: _Optional[int] = ...) -> None: ...

class Task(_message.Message):
    __slots__ = ["task_spec"]
    TASK_SPEC_FIELD_NUMBER: _ClassVar[int]
    task_spec: TaskSpec
    def __init__(self, task_spec: _Optional[_Union[TaskSpec, _Mapping]] = ...) -> None: ...

class ResourceId(_message.Message):
    __slots__ = ["index", "quantity"]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    index: int
    quantity: float
    def __init__(self, index: _Optional[int] = ..., quantity: _Optional[float] = ...) -> None: ...

class ResourceMapEntry(_message.Message):
    __slots__ = ["name", "resource_ids"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_IDS_FIELD_NUMBER: _ClassVar[int]
    name: str
    resource_ids: _containers.RepeatedCompositeFieldContainer[ResourceId]
    def __init__(self, name: _Optional[str] = ..., resource_ids: _Optional[_Iterable[_Union[ResourceId, _Mapping]]] = ...) -> None: ...

class ViewData(_message.Message):
    __slots__ = ["view_name", "measures"]
    class Measure(_message.Message):
        __slots__ = ["tags", "int_value", "double_value", "distribution_min", "distribution_mean", "distribution_max", "distribution_count", "distribution_bucket_boundaries", "distribution_bucket_counts"]
        TAGS_FIELD_NUMBER: _ClassVar[int]
        INT_VALUE_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_MIN_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_MEAN_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_MAX_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_COUNT_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_BUCKET_BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
        DISTRIBUTION_BUCKET_COUNTS_FIELD_NUMBER: _ClassVar[int]
        tags: str
        int_value: int
        double_value: float
        distribution_min: float
        distribution_mean: float
        distribution_max: float
        distribution_count: float
        distribution_bucket_boundaries: _containers.RepeatedScalarFieldContainer[float]
        distribution_bucket_counts: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, tags: _Optional[str] = ..., int_value: _Optional[int] = ..., double_value: _Optional[float] = ..., distribution_min: _Optional[float] = ..., distribution_mean: _Optional[float] = ..., distribution_max: _Optional[float] = ..., distribution_count: _Optional[float] = ..., distribution_bucket_boundaries: _Optional[_Iterable[float]] = ..., distribution_bucket_counts: _Optional[_Iterable[float]] = ...) -> None: ...
    VIEW_NAME_FIELD_NUMBER: _ClassVar[int]
    MEASURES_FIELD_NUMBER: _ClassVar[int]
    view_name: str
    measures: _containers.RepeatedCompositeFieldContainer[ViewData.Measure]
    def __init__(self, view_name: _Optional[str] = ..., measures: _Optional[_Iterable[_Union[ViewData.Measure, _Mapping]]] = ...) -> None: ...

class ObjectRefInfo(_message.Message):
    __slots__ = ["object_id", "call_site", "object_size", "local_ref_count", "submitted_task_ref_count", "contained_in_owned", "pinned_in_memory", "task_status", "attempt_number"]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    CALL_SITE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_SIZE_FIELD_NUMBER: _ClassVar[int]
    LOCAL_REF_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_TASK_REF_COUNT_FIELD_NUMBER: _ClassVar[int]
    CONTAINED_IN_OWNED_FIELD_NUMBER: _ClassVar[int]
    PINNED_IN_MEMORY_FIELD_NUMBER: _ClassVar[int]
    TASK_STATUS_FIELD_NUMBER: _ClassVar[int]
    ATTEMPT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    object_id: bytes
    call_site: str
    object_size: int
    local_ref_count: int
    submitted_task_ref_count: int
    contained_in_owned: _containers.RepeatedScalarFieldContainer[bytes]
    pinned_in_memory: bool
    task_status: TaskStatus
    attempt_number: int
    def __init__(self, object_id: _Optional[bytes] = ..., call_site: _Optional[str] = ..., object_size: _Optional[int] = ..., local_ref_count: _Optional[int] = ..., submitted_task_ref_count: _Optional[int] = ..., contained_in_owned: _Optional[_Iterable[bytes]] = ..., pinned_in_memory: bool = ..., task_status: _Optional[_Union[TaskStatus, str]] = ..., attempt_number: _Optional[int] = ...) -> None: ...

class ResourceAllocations(_message.Message):
    __slots__ = ["resource_slots"]
    class ResourceSlot(_message.Message):
        __slots__ = ["slot", "allocation"]
        SLOT_FIELD_NUMBER: _ClassVar[int]
        ALLOCATION_FIELD_NUMBER: _ClassVar[int]
        slot: int
        allocation: float
        def __init__(self, slot: _Optional[int] = ..., allocation: _Optional[float] = ...) -> None: ...
    RESOURCE_SLOTS_FIELD_NUMBER: _ClassVar[int]
    resource_slots: _containers.RepeatedCompositeFieldContainer[ResourceAllocations.ResourceSlot]
    def __init__(self, resource_slots: _Optional[_Iterable[_Union[ResourceAllocations.ResourceSlot, _Mapping]]] = ...) -> None: ...

class CoreWorkerStats(_message.Message):
    __slots__ = ["num_pending_tasks", "num_object_refs_in_scope", "ip_address", "port", "actor_id", "used_resources", "webui_display", "num_in_plasma", "num_local_objects", "used_object_store_memory", "task_queue_length", "num_executed_tasks", "actor_title", "object_refs", "job_id", "worker_id", "language", "pid", "worker_type", "objects_total", "num_owned_objects", "num_owned_actors", "num_running_tasks"]
    class UsedResourcesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ResourceAllocations
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ResourceAllocations, _Mapping]] = ...) -> None: ...
    class WebuiDisplayEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NUM_PENDING_TASKS_FIELD_NUMBER: _ClassVar[int]
    NUM_OBJECT_REFS_IN_SCOPE_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    USED_RESOURCES_FIELD_NUMBER: _ClassVar[int]
    WEBUI_DISPLAY_FIELD_NUMBER: _ClassVar[int]
    NUM_IN_PLASMA_FIELD_NUMBER: _ClassVar[int]
    NUM_LOCAL_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    USED_OBJECT_STORE_MEMORY_FIELD_NUMBER: _ClassVar[int]
    TASK_QUEUE_LENGTH_FIELD_NUMBER: _ClassVar[int]
    NUM_EXECUTED_TASKS_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TITLE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_REFS_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    WORKER_TYPE_FIELD_NUMBER: _ClassVar[int]
    OBJECTS_TOTAL_FIELD_NUMBER: _ClassVar[int]
    NUM_OWNED_OBJECTS_FIELD_NUMBER: _ClassVar[int]
    NUM_OWNED_ACTORS_FIELD_NUMBER: _ClassVar[int]
    NUM_RUNNING_TASKS_FIELD_NUMBER: _ClassVar[int]
    num_pending_tasks: int
    num_object_refs_in_scope: int
    ip_address: str
    port: int
    actor_id: bytes
    used_resources: _containers.MessageMap[str, ResourceAllocations]
    webui_display: _containers.ScalarMap[str, str]
    num_in_plasma: int
    num_local_objects: int
    used_object_store_memory: int
    task_queue_length: int
    num_executed_tasks: int
    actor_title: str
    object_refs: _containers.RepeatedCompositeFieldContainer[ObjectRefInfo]
    job_id: bytes
    worker_id: bytes
    language: Language
    pid: int
    worker_type: WorkerType
    objects_total: int
    num_owned_objects: int
    num_owned_actors: int
    num_running_tasks: int
    def __init__(self, num_pending_tasks: _Optional[int] = ..., num_object_refs_in_scope: _Optional[int] = ..., ip_address: _Optional[str] = ..., port: _Optional[int] = ..., actor_id: _Optional[bytes] = ..., used_resources: _Optional[_Mapping[str, ResourceAllocations]] = ..., webui_display: _Optional[_Mapping[str, str]] = ..., num_in_plasma: _Optional[int] = ..., num_local_objects: _Optional[int] = ..., used_object_store_memory: _Optional[int] = ..., task_queue_length: _Optional[int] = ..., num_executed_tasks: _Optional[int] = ..., actor_title: _Optional[str] = ..., object_refs: _Optional[_Iterable[_Union[ObjectRefInfo, _Mapping]]] = ..., job_id: _Optional[bytes] = ..., worker_id: _Optional[bytes] = ..., language: _Optional[_Union[Language, str]] = ..., pid: _Optional[int] = ..., worker_type: _Optional[_Union[WorkerType, str]] = ..., objects_total: _Optional[int] = ..., num_owned_objects: _Optional[int] = ..., num_owned_actors: _Optional[int] = ..., num_running_tasks: _Optional[int] = ...) -> None: ...

class NodeResourceUsage(_message.Message):
    __slots__ = ["json"]
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class MetricPoint(_message.Message):
    __slots__ = ["metric_name", "timestamp", "value", "tags", "description", "units"]
    class TagsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    METRIC_NAME_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    UNITS_FIELD_NUMBER: _ClassVar[int]
    metric_name: str
    timestamp: int
    value: float
    tags: _containers.ScalarMap[str, str]
    description: str
    units: str
    def __init__(self, metric_name: _Optional[str] = ..., timestamp: _Optional[int] = ..., value: _Optional[float] = ..., tags: _Optional[_Mapping[str, str]] = ..., description: _Optional[str] = ..., units: _Optional[str] = ...) -> None: ...

class NamedActorInfo(_message.Message):
    __slots__ = ["ray_namespace", "name"]
    RAY_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ray_namespace: str
    name: str
    def __init__(self, ray_namespace: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...
