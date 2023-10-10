from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class LogBatch(_message.Message):
    __slots__ = ["ip", "pid", "job_id", "is_error", "lines", "actor_name", "task_name"]
    IP_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    IS_ERROR_FIELD_NUMBER: _ClassVar[int]
    LINES_FIELD_NUMBER: _ClassVar[int]
    ACTOR_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    ip: str
    pid: str
    job_id: str
    is_error: bool
    lines: _containers.RepeatedScalarFieldContainer[str]
    actor_name: str
    task_name: str
    def __init__(self, ip: _Optional[str] = ..., pid: _Optional[str] = ..., job_id: _Optional[str] = ..., is_error: bool = ..., lines: _Optional[_Iterable[str]] = ..., actor_name: _Optional[str] = ..., task_name: _Optional[str] = ...) -> None: ...
