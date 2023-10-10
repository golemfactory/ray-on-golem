from src.ray.protobuf import common_pb2 as _common_pb2
from src.ray.protobuf import dependency_pb2 as _dependency_pb2
from src.ray.protobuf import gcs_pb2 as _gcs_pb2
from src.ray.protobuf import logging_pb2 as _logging_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChannelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    WORKER_OBJECT_EVICTION: _ClassVar[ChannelType]
    WORKER_REF_REMOVED_CHANNEL: _ClassVar[ChannelType]
    WORKER_OBJECT_LOCATIONS_CHANNEL: _ClassVar[ChannelType]
    GCS_ACTOR_CHANNEL: _ClassVar[ChannelType]
    GCS_JOB_CHANNEL: _ClassVar[ChannelType]
    GCS_NODE_INFO_CHANNEL: _ClassVar[ChannelType]
    GCS_WORKER_DELTA_CHANNEL: _ClassVar[ChannelType]
    RAY_ERROR_INFO_CHANNEL: _ClassVar[ChannelType]
    RAY_LOG_CHANNEL: _ClassVar[ChannelType]
    RAY_PYTHON_FUNCTION_CHANNEL: _ClassVar[ChannelType]
    RAY_NODE_RESOURCE_USAGE_CHANNEL: _ClassVar[ChannelType]
WORKER_OBJECT_EVICTION: ChannelType
WORKER_REF_REMOVED_CHANNEL: ChannelType
WORKER_OBJECT_LOCATIONS_CHANNEL: ChannelType
GCS_ACTOR_CHANNEL: ChannelType
GCS_JOB_CHANNEL: ChannelType
GCS_NODE_INFO_CHANNEL: ChannelType
GCS_WORKER_DELTA_CHANNEL: ChannelType
RAY_ERROR_INFO_CHANNEL: ChannelType
RAY_LOG_CHANNEL: ChannelType
RAY_PYTHON_FUNCTION_CHANNEL: ChannelType
RAY_NODE_RESOURCE_USAGE_CHANNEL: ChannelType

class PubMessage(_message.Message):
    __slots__ = ["channel_type", "key_id", "worker_object_eviction_message", "worker_ref_removed_message", "worker_object_locations_message", "actor_message", "job_message", "node_info_message", "node_resource_message", "worker_delta_message", "error_info_message", "log_batch_message", "python_function_message", "node_resource_usage_message", "failure_message", "sequence_id"]
    CHANNEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_ID_FIELD_NUMBER: _ClassVar[int]
    WORKER_OBJECT_EVICTION_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    WORKER_REF_REMOVED_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    WORKER_OBJECT_LOCATIONS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ACTOR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    JOB_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NODE_INFO_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NODE_RESOURCE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    WORKER_DELTA_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_INFO_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    LOG_BATCH_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PYTHON_FUNCTION_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NODE_RESOURCE_USAGE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FAILURE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_ID_FIELD_NUMBER: _ClassVar[int]
    channel_type: ChannelType
    key_id: bytes
    worker_object_eviction_message: WorkerObjectEvictionMessage
    worker_ref_removed_message: WorkerRefRemovedMessage
    worker_object_locations_message: WorkerObjectLocationsPubMessage
    actor_message: _gcs_pb2.ActorTableData
    job_message: _gcs_pb2.JobTableData
    node_info_message: _gcs_pb2.GcsNodeInfo
    node_resource_message: _gcs_pb2.NodeResourceChange
    worker_delta_message: _gcs_pb2.WorkerDeltaData
    error_info_message: _gcs_pb2.ErrorTableData
    log_batch_message: _logging_pb2.LogBatch
    python_function_message: _dependency_pb2.PythonFunction
    node_resource_usage_message: _common_pb2.NodeResourceUsage
    failure_message: FailureMessage
    sequence_id: int
    def __init__(self, channel_type: _Optional[_Union[ChannelType, str]] = ..., key_id: _Optional[bytes] = ..., worker_object_eviction_message: _Optional[_Union[WorkerObjectEvictionMessage, _Mapping]] = ..., worker_ref_removed_message: _Optional[_Union[WorkerRefRemovedMessage, _Mapping]] = ..., worker_object_locations_message: _Optional[_Union[WorkerObjectLocationsPubMessage, _Mapping]] = ..., actor_message: _Optional[_Union[_gcs_pb2.ActorTableData, _Mapping]] = ..., job_message: _Optional[_Union[_gcs_pb2.JobTableData, _Mapping]] = ..., node_info_message: _Optional[_Union[_gcs_pb2.GcsNodeInfo, _Mapping]] = ..., node_resource_message: _Optional[_Union[_gcs_pb2.NodeResourceChange, _Mapping]] = ..., worker_delta_message: _Optional[_Union[_gcs_pb2.WorkerDeltaData, _Mapping]] = ..., error_info_message: _Optional[_Union[_gcs_pb2.ErrorTableData, _Mapping]] = ..., log_batch_message: _Optional[_Union[_logging_pb2.LogBatch, _Mapping]] = ..., python_function_message: _Optional[_Union[_dependency_pb2.PythonFunction, _Mapping]] = ..., node_resource_usage_message: _Optional[_Union[_common_pb2.NodeResourceUsage, _Mapping]] = ..., failure_message: _Optional[_Union[FailureMessage, _Mapping]] = ..., sequence_id: _Optional[int] = ...) -> None: ...

class WorkerObjectEvictionMessage(_message.Message):
    __slots__ = ["object_id"]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    object_id: bytes
    def __init__(self, object_id: _Optional[bytes] = ...) -> None: ...

class WorkerRefRemovedMessage(_message.Message):
    __slots__ = ["borrowed_refs"]
    BORROWED_REFS_FIELD_NUMBER: _ClassVar[int]
    borrowed_refs: _containers.RepeatedCompositeFieldContainer[_common_pb2.ObjectReferenceCount]
    def __init__(self, borrowed_refs: _Optional[_Iterable[_Union[_common_pb2.ObjectReferenceCount, _Mapping]]] = ...) -> None: ...

class WorkerObjectLocationsPubMessage(_message.Message):
    __slots__ = ["node_ids", "object_size", "spilled_url", "spilled_node_id", "primary_node_id", "ref_removed", "pending_creation", "did_spill"]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    OBJECT_SIZE_FIELD_NUMBER: _ClassVar[int]
    SPILLED_URL_FIELD_NUMBER: _ClassVar[int]
    SPILLED_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_NODE_ID_FIELD_NUMBER: _ClassVar[int]
    REF_REMOVED_FIELD_NUMBER: _ClassVar[int]
    PENDING_CREATION_FIELD_NUMBER: _ClassVar[int]
    DID_SPILL_FIELD_NUMBER: _ClassVar[int]
    node_ids: _containers.RepeatedScalarFieldContainer[bytes]
    object_size: int
    spilled_url: str
    spilled_node_id: bytes
    primary_node_id: bytes
    ref_removed: bool
    pending_creation: bool
    did_spill: bool
    def __init__(self, node_ids: _Optional[_Iterable[bytes]] = ..., object_size: _Optional[int] = ..., spilled_url: _Optional[str] = ..., spilled_node_id: _Optional[bytes] = ..., primary_node_id: _Optional[bytes] = ..., ref_removed: bool = ..., pending_creation: bool = ..., did_spill: bool = ...) -> None: ...

class FailureMessage(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Command(_message.Message):
    __slots__ = ["channel_type", "key_id", "unsubscribe_message", "subscribe_message"]
    CHANNEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_ID_FIELD_NUMBER: _ClassVar[int]
    UNSUBSCRIBE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    channel_type: ChannelType
    key_id: bytes
    unsubscribe_message: UnsubscribeMessage
    subscribe_message: SubMessage
    def __init__(self, channel_type: _Optional[_Union[ChannelType, str]] = ..., key_id: _Optional[bytes] = ..., unsubscribe_message: _Optional[_Union[UnsubscribeMessage, _Mapping]] = ..., subscribe_message: _Optional[_Union[SubMessage, _Mapping]] = ...) -> None: ...

class UnsubscribeMessage(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class SubMessage(_message.Message):
    __slots__ = ["worker_object_eviction_message", "worker_ref_removed_message", "worker_object_locations_message"]
    WORKER_OBJECT_EVICTION_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    WORKER_REF_REMOVED_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    WORKER_OBJECT_LOCATIONS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    worker_object_eviction_message: WorkerObjectEvictionSubMessage
    worker_ref_removed_message: WorkerRefRemovedSubMessage
    worker_object_locations_message: WorkerObjectLocationsSubMessage
    def __init__(self, worker_object_eviction_message: _Optional[_Union[WorkerObjectEvictionSubMessage, _Mapping]] = ..., worker_ref_removed_message: _Optional[_Union[WorkerRefRemovedSubMessage, _Mapping]] = ..., worker_object_locations_message: _Optional[_Union[WorkerObjectLocationsSubMessage, _Mapping]] = ...) -> None: ...

class WorkerObjectEvictionSubMessage(_message.Message):
    __slots__ = ["intended_worker_id", "object_id", "subscriber_address", "generator_id"]
    INTENDED_WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBER_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    GENERATOR_ID_FIELD_NUMBER: _ClassVar[int]
    intended_worker_id: bytes
    object_id: bytes
    subscriber_address: _common_pb2.Address
    generator_id: bytes
    def __init__(self, intended_worker_id: _Optional[bytes] = ..., object_id: _Optional[bytes] = ..., subscriber_address: _Optional[_Union[_common_pb2.Address, _Mapping]] = ..., generator_id: _Optional[bytes] = ...) -> None: ...

class WorkerRefRemovedSubMessage(_message.Message):
    __slots__ = ["intended_worker_id", "reference", "contained_in_id", "subscriber_worker_id"]
    INTENDED_WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    CONTAINED_IN_ID_FIELD_NUMBER: _ClassVar[int]
    SUBSCRIBER_WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    intended_worker_id: bytes
    reference: _common_pb2.ObjectReference
    contained_in_id: bytes
    subscriber_worker_id: bytes
    def __init__(self, intended_worker_id: _Optional[bytes] = ..., reference: _Optional[_Union[_common_pb2.ObjectReference, _Mapping]] = ..., contained_in_id: _Optional[bytes] = ..., subscriber_worker_id: _Optional[bytes] = ...) -> None: ...

class WorkerObjectLocationsSubMessage(_message.Message):
    __slots__ = ["intended_worker_id", "object_id"]
    INTENDED_WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    intended_worker_id: bytes
    object_id: bytes
    def __init__(self, intended_worker_id: _Optional[bytes] = ..., object_id: _Optional[bytes] = ...) -> None: ...

class PubsubLongPollingRequest(_message.Message):
    __slots__ = ["subscriber_id", "max_processed_sequence_id", "publisher_id"]
    SUBSCRIBER_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_PROCESSED_SEQUENCE_ID_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_ID_FIELD_NUMBER: _ClassVar[int]
    subscriber_id: bytes
    max_processed_sequence_id: int
    publisher_id: bytes
    def __init__(self, subscriber_id: _Optional[bytes] = ..., max_processed_sequence_id: _Optional[int] = ..., publisher_id: _Optional[bytes] = ...) -> None: ...

class PubsubLongPollingReply(_message.Message):
    __slots__ = ["pub_messages", "publisher_id"]
    PUB_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    PUBLISHER_ID_FIELD_NUMBER: _ClassVar[int]
    pub_messages: _containers.RepeatedCompositeFieldContainer[PubMessage]
    publisher_id: bytes
    def __init__(self, pub_messages: _Optional[_Iterable[_Union[PubMessage, _Mapping]]] = ..., publisher_id: _Optional[bytes] = ...) -> None: ...

class PubsubCommandBatchRequest(_message.Message):
    __slots__ = ["subscriber_id", "commands"]
    SUBSCRIBER_ID_FIELD_NUMBER: _ClassVar[int]
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    subscriber_id: bytes
    commands: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(self, subscriber_id: _Optional[bytes] = ..., commands: _Optional[_Iterable[_Union[Command, _Mapping]]] = ...) -> None: ...

class PubsubCommandBatchReply(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
