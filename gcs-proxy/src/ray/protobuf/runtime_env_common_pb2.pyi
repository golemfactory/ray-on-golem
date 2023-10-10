from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RuntimeEnvUris(_message.Message):
    __slots__ = ["working_dir_uri", "py_modules_uris"]
    WORKING_DIR_URI_FIELD_NUMBER: _ClassVar[int]
    PY_MODULES_URIS_FIELD_NUMBER: _ClassVar[int]
    working_dir_uri: str
    py_modules_uris: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, working_dir_uri: _Optional[str] = ..., py_modules_uris: _Optional[_Iterable[str]] = ...) -> None: ...

class RuntimeEnvConfig(_message.Message):
    __slots__ = ["setup_timeout_seconds", "eager_install"]
    SETUP_TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    EAGER_INSTALL_FIELD_NUMBER: _ClassVar[int]
    setup_timeout_seconds: int
    eager_install: bool
    def __init__(self, setup_timeout_seconds: _Optional[int] = ..., eager_install: bool = ...) -> None: ...

class RuntimeEnvInfo(_message.Message):
    __slots__ = ["serialized_runtime_env", "uris", "runtime_env_config"]
    SERIALIZED_RUNTIME_ENV_FIELD_NUMBER: _ClassVar[int]
    URIS_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_ENV_CONFIG_FIELD_NUMBER: _ClassVar[int]
    serialized_runtime_env: str
    uris: RuntimeEnvUris
    runtime_env_config: RuntimeEnvConfig
    def __init__(self, serialized_runtime_env: _Optional[str] = ..., uris: _Optional[_Union[RuntimeEnvUris, _Mapping]] = ..., runtime_env_config: _Optional[_Union[RuntimeEnvConfig, _Mapping]] = ...) -> None: ...

class RuntimeEnvState(_message.Message):
    __slots__ = ["runtime_env", "ref_cnt", "success", "error", "creation_time_ms"]
    RUNTIME_ENV_FIELD_NUMBER: _ClassVar[int]
    REF_CNT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    CREATION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    runtime_env: str
    ref_cnt: int
    success: bool
    error: str
    creation_time_ms: int
    def __init__(self, runtime_env: _Optional[str] = ..., ref_cnt: _Optional[int] = ..., success: bool = ..., error: _Optional[str] = ..., creation_time_ms: _Optional[int] = ...) -> None: ...
