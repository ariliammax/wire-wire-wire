# serialization.py
# in chat.common

from chat.common.config import Config
from math import log
from typing import Callable, Optional


# this is supposed to be ceiling(log_2(...) / 8), but too lazy to calculate
# that.
# the reason for that function:
# `int.to_bytes(length=num_chars, byteorder='little')` uses ASCII
# to encode the `int`, which is 256, i.e. 2 ** 8, i.e. log_2 / 8, to find the
# number of `char`s.
# anyways, this isn't exactly that, but a safe over-approximation.
INT_LEN_BITS = int(log(Config.INT_MAX_LEN) / 8) + 1
LIST_LEN_BITS = int(log(Config.LIST_MAX_LEN) / 8) + 1
STR_LEN_BITS = int(log(Config.STR_MAX_LEN) / 8) + 1


class SerializationUtils:

    @staticmethod
    def deserialize_bool(data: bytes) -> bool:
        return bool.from_bytes(data, byteorder='little')

    @staticmethod
    def serialize_bool(val: bool) -> bytes:
        return val.to_bytes(1, byteorder='little')

    @staticmethod
    def deserialize_int(data: bytes) -> int:
        return int.from_bytes(data, byteorder='little')

    @staticmethod
    def serialize_int(val: int, length: int = INT_LEN_BITS) -> bytes:
        return val.to_bytes(length, byteorder='little')

    @staticmethod
    def deserialize_str(data: bytes) -> str:
        length = SerializationUtils.deserialize_int(data[:STR_LEN_BITS])
        return data[STR_LEN_BITS:length + STR_LEN_BITS].decode('utf-8')

    @staticmethod
    def serialize_str(val: str) -> bytes:
        encoded = val.encode('utf-8')
        return SerializationUtils.serialize_int(
            len(encoded),
            STR_LEN_BITS) + encoded

    @staticmethod
    def deserialize_list(data: bytes,
                         item_deserialize: Callable,
                         item_serialize: Callable,
                         remain: Optional[int] = None) -> bytes:
        if remain is None:
            length = SerializationUtils.deserialize_int(data[:LIST_LEN_BITS])
            return SerializationUtils.deserialize_list(data[LIST_LEN_BITS:],
                                                       item_deserialize,
                                                       item_serialize,
                                                       remain=length)
        elif remain == 0:
            return []
        else:
            obj = item_deserialize(data)
            length = len(item_serialize(obj))
            return [obj] + SerializationUtils.deserialize_list(
                data[length:],
                item_deserialize,
                item_serialize,
                remain=remain - 1)

    @staticmethod
    def serialize_list(val: list,
                       item_serialize: Callable,
                       remain: Optional[int] = None) -> bytes:
        if remain is None:
            return (SerializationUtils.serialize_int(len(val),
                                                     LIST_LEN_BITS) +
                    SerializationUtils.serialize_list(val,
                                                      item_serialize,
                                                      remain=len(val)))
        elif remain == 0:
            return b''
        else:
            return (item_serialize(val[0]) +
                    SerializationUtils.serialize_list(val[1:],
                                                      item_serialize,
                                                      remain=remain - 1))
