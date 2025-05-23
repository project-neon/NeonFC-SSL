# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ssl_gc_geometry.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ssl_gc_geometry.proto',
  package='',
  syntax='proto2',
  serialized_options=_b('Z<github.com/RoboCup-SSL/ssl-game-controller/internal/app/geom'),
  serialized_pb=_b('\n\x15ssl_gc_geometry.proto\"\x1f\n\x07Vector2\x12\t\n\x01x\x18\x01 \x02(\x02\x12\t\n\x01y\x18\x02 \x02(\x02\"*\n\x07Vector3\x12\t\n\x01x\x18\x01 \x02(\x02\x12\t\n\x01y\x18\x02 \x02(\x02\x12\t\n\x01z\x18\x03 \x02(\x02\x42>Z<github.com/RoboCup-SSL/ssl-game-controller/internal/app/geom')
)




_VECTOR2 = _descriptor.Descriptor(
  name='Vector2',
  full_name='Vector2',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='Vector2.x', index=0,
      number=1, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='Vector2.y', index=1,
      number=2, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=25,
  serialized_end=56,
)


_VECTOR3 = _descriptor.Descriptor(
  name='Vector3',
  full_name='Vector3',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='Vector3.x', index=0,
      number=1, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='Vector3.y', index=1,
      number=2, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='z', full_name='Vector3.z', index=2,
      number=3, type=2, cpp_type=6, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=58,
  serialized_end=100,
)

DESCRIPTOR.message_types_by_name['Vector2'] = _VECTOR2
DESCRIPTOR.message_types_by_name['Vector3'] = _VECTOR3
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Vector2 = _reflection.GeneratedProtocolMessageType('Vector2', (_message.Message,), dict(
  DESCRIPTOR = _VECTOR2,
  __module__ = 'ssl_gc_geometry_pb2'
  # @@protoc_insertion_point(class_scope:Vector2)
  ))
_sym_db.RegisterMessage(Vector2)

Vector3 = _reflection.GeneratedProtocolMessageType('Vector3', (_message.Message,), dict(
  DESCRIPTOR = _VECTOR3,
  __module__ = 'ssl_gc_geometry_pb2'
  # @@protoc_insertion_point(class_scope:Vector3)
  ))
_sym_db.RegisterMessage(Vector3)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
