# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: src/ray/protobuf/logging.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1esrc/ray/protobuf/logging.proto\x12\x07ray.rpc\"{\n\x08LogBatch\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\t\x12\x0e\n\x06job_id\x18\x03 \x01(\t\x12\x10\n\x08is_error\x18\x04 \x01(\x08\x12\r\n\x05lines\x18\x05 \x03(\t\x12\x12\n\nactor_name\x18\x06 \x01(\t\x12\x11\n\ttask_name\x18\x07 \x01(\tB\x03\xf8\x01\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'src.ray.protobuf.logging_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\370\001\001'
  _globals['_LOGBATCH']._serialized_start=43
  _globals['_LOGBATCH']._serialized_end=166
# @@protoc_insertion_point(module_scope)
