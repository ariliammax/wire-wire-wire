# util.py
# in chat.common

import builtins

from chat.common.serialization import SerializationUtils
from enum import Enum, EnumMeta
from typing import Callable, Dict, List, Optional, Type


class Interface(object):
    """An abstract `interface` that will be used in e.g. `model_from_proto`
       to autogenerate the sort of useful code we would like.

        attributes:
          `_fields_enum`: An `Enum` subclass which has members of the names
                          of the field name and values of the field type.
    """
    _fields_enum: Optional[type] = None


class Model(object):
    """The abstract "models" created from `interface`s.
       Useful for making new models, or (de)serializing.
    """
    _fields: Dict[str, type] = {}

    _field_deserializers: Dict[str, Callable] = {}

    _field_serializers: Dict[str, Callable] = {}

    _order_of_fields: List[str] = {}

    # TODO: is this necessary? I think not necessarily, but will
    # be at a minimum useful for awkard class attributes sharing object
    # attributes names, so best to just discourage it entirely.
    _reserved_fields = ['fields',
                        'field_deserializers',
                        'field_serializers',
                        'order_of_fields',
                        'reserved_fields']

    @staticmethod
    def default_deserializer(t: Type) -> Optional[Callable]:
        match t:
            case builtins.bool:
                return SerializationUtils.deserialize_bool
            case builtins.int:
                return SerializationUtils.deserialize_int
            case builtins.str:
                return SerializationUtils.deserialize_str
            case _:
                if issubclass(t, Model):
                    return t.deserialize

    @staticmethod
    def default_serializer(t: Type) -> Optional[Callable]:
        match t:
            case builtins.bool:
                return SerializationUtils.serialize_bool
            case builtins.int:
                return SerializationUtils.serialize_int
            case builtins.str:
                return SerializationUtils.serialize_str
            case _:
                if issubclass(t, Model):
                    return lambda x: x.serialize()
                return None

    @staticmethod
    def default_list_deserializer(t: Type) -> Callable:
        return (lambda d: SerializationUtils.deserialize_list(
                    d,
                    Model.default_deserializer(t),
                    Model.default_serializer(t)))

    @staticmethod
    def default_list_serializer(t: Type) -> Callable:
        return (lambda v: SerializationUtils.serialize_list(
                    v,
                    Model.default_serializer(t)))

    @classmethod
    def deserialize(cls, data: bytes):
        # TODO: this can get screw-y with optionals.
        # a janky way of doing it without more code would be just doing it
        # on lists (of max len 1).
        obj = cls()
        for name in cls._order_of_fields:
            deserializer = cls._field_deserializers[name]
            serializer = cls._field_serializers[name]

            field_val = deserializer(data)
            length = len(serializer(field_val))

            getattr(obj, f'set_{name!s}', lambda _: obj)(field_val)
            try:
                data = data[length:]
            except Exception:
                break
        return obj

    def serialize(self) -> bytes:
        return b''.join(self._field_serializers[name](getattr(self,
                                                              f'get_{name!s}',
                                                              lambda: None)())
                        for name in self._order_of_fields)

    def as_model(self, model: Type):
        obj = model()
        for name in self._fields:
            getattr(obj, f'set_{name!s}', lambda _: obj)(
                getattr(self, f'get_{name!s}', lambda: None)())
        return obj

    @staticmethod
    def model_with_fields(field_deserializers: Dict[str, Callable] = {},
                          field_serializers: Dict[str, Callable] = {},
                          order_of_fields: List[str] = None,
                          **fields: Dict[str, type]) -> type:
        for name in fields:
            if name in Model._reserved_fields:
                raise ValueError(f'Field \'{name!s}\' is a reserved name.')

        # this gives the explicit order, or just uses the keys.
        order = order_of_fields or list(fields.keys())

        # set default (de)serializers, if not set
        for name, t in fields.items():
            deserialize = field_deserializers.get(
                name, Model.default_deserializer(t))
            serialize = field_serializers.get(
                name, Model.default_serializer(t))

            if serialize is None or deserialize is None:
                raise ValueError(f'Field {name!s} requires a ' +
                                 ('(de)' if deserialize is None
                                  and serialize is None else
                                  'de' if deserialize is None else '') +
                                 'serializer.')

            field_deserializers[name] = deserialize
            field_serializers[name] = serialize

        class __impl_model__(Model):
            # copy is likely safest here...
            _fields = {k: v for k, v in fields.items()}

            _field_deserializers = {k: v
                                    for k, v in field_deserializers.items()}

            _field_serializers = {k: v for k, v in field_serializers.items()}

            _order_of_fields = order

        return __impl_model__.add_getters_setters()

    @classmethod
    def add_getters_setters(model):
        for name, value in model._fields.items():

            if type(value) is not type:
                raise ValueError(f'Field \'{name!s}\' with value '
                                 f'\'{value!r}\' which is not a `type`.')

            # note: you do NOT want to put `private_name` within any of the
            #       implementations that will be `setattr`ed, since then
            #       `private_name` the variable will be bound to the function.
            #       Another way would be to explicitly `del` it, but uh, that's
            #       not very pythonic...
            #
            #       For some stupid, hacky reason the default works.
            #       I guess since it puts it in the function's `__defaults__`
            #       attribute...
            private_name = f'_{name!s}'

            # the getter we'll add to `model`.
            def __impl_setter__(self: model,
                                val: Optional[value],
                                private_name: str = private_name):
                setattr(self, private_name, val)
                return self

            setattr(model, f'set_{name!s}', __impl_setter__)

            # the setter we'll add to `model`.
            def __impl_getter__(self: model,
                                private_name: str = private_name):
                return getattr(self, private_name, None)

            setattr(model, f'get_{name!s}', __impl_getter__)

        # the `__init__` we'll add to `model`.
        # this might get weird with inheritence, but as long as the inherited
        # call `add_getters_setters`, then we should be good.
        def __impl_init__(self, **kwargs) -> model:
            for name in self._fields:
                if name in kwargs:
                    getattr(self, f'set_{name!s}', lambda _: _)(kwargs
                                                                [name])
                else:
                    setattr(self, f'_{name!s}', None)

        setattr(model, '__init__', __impl_init__)

        return model.clean_getters_setters()

    @classmethod
    def clean_getters_setters(model):
        for attr_name in dir(model):
            match attr_name[:4]:
                case 'get_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
                case 'set_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
        return model

    @classmethod
    def add_fields(cls,
                   field_deserializers: Dict[str, Callable] = {},
                   field_serializers: Dict[str, Callable] = {},
                   order_of_fields: List[str] = None,
                   **new_fields: Dict[str, type]) -> type:
        return Model.model_with_fields(
            field_deserializers=field_deserializers,
            field_serializers=field_serializers,
            order_of_fields=order_of_fields,
            **dict(list(cls._fields.items()) +
                   list(new_fields.items()))).add_getters_setters()

    @classmethod
    def omit_fields(cls,
                    field_deserializers: Dict[str, Callable] = {},
                    field_serializers: Dict[str, Callable] = {},
                    order_of_fields: List[str] = None,
                    **rm_fields: Dict[str, type]) -> type:
        for fname in rm_fields:
            if fname not in cls._fields:
                raise ValueError(f'Cannot omit field \'{fname!s}\'; '
                                 f'it is not a field of {cls!s}.')
        return Model.model_with_fields(
            field_deserializers=field_deserializers,
            field_serializers=field_serializers,
            order_of_fields=order_of_fields,
            **{n: t for n, t in cls._fields.items()
               if n not in rm_fields}).add_getters_setters()


def model_from_proto(iface: type) -> type:
    """Materializes a class with getters and setters from an interface.

        Raises: A `ValueError` if `iface` is not `interface` subclass,
                               if `iface._fields_enum` is not `Enum` subclass
                               if `iface._fields_enum`'s members do not have
                                 `str` names and `type` values.

        Returns: A `class` generated by the `iface : interface`.
    """
    if not issubclass(iface, Interface):
        raise ValueError(f'Arg `iface` ({iface!r}) is not a subclass of '
                         f'`interface` (type is {type(iface)!r}).')

    if not hasattr(iface, '_fields_enum'):
        raise ValueError(f'Arg `iface` ({iface!r}) does not have a '
                         f'`_fields_enum` attribute.')

    not_enum = False
    if (type(iface._fields_enum) is not Enum and
            type(iface._fields_enum) is not EnumMeta):
        not_enum = True

    if not not_enum:
        if (not issubclass(iface._fields_enum, Enum) and
                not issubclass(iface._fields_enum, EnumMeta)):
            not_enum = True

    if not_enum:
        raise ValueError(f'Arg `iface`\'s `_fields_enum` attribute '
                         f'({iface._fields_enum!r}) is not an `Enum` '
                         f'(type is {type(iface._fields_enum)!r}).')

    # we may iterate an `Enum`'s members dictionary by `__members__`.
    return Model.model_from_fields(**dict([(member.name, member.value)
                                           for _, member in
                                           iface._fields_enum.__members__
                                           .items()]))
