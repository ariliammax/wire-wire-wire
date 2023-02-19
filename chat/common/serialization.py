# serialization.py
# in chat.common

from chat.common.config import Config


# this is supposed to be ceiling(log_2(...) / 8), but too lazy to calculate
# that.
# the reason for that function:
# `int.to_bytes(length=num_chars, byteorder='little')` uses ASCII
# to encode the `int`, which is 256, i.e. 2 ** 8, i.e. log_2 / 8, to find the
# number of `char`s.
# anyways, this isn't exactly that, but a safe over-approximation.
from math import log
STR_LEN_BITS = int(log(Config.STR_MAX_LEN) / 8) + 1


class ModelSerializationUtils:

    @staticmethod
    def serialize_int(val: int) -> bytes:
        return val.to_bytes(STR_LEN_BITS, byteorder='little')

    @staticmethod
    def deserialize_int(data: bytes) -> int:
        return int.from_bytes(data, byteorder='little')

    @staticmethod
    def serialize_str(val: str) -> bytes:
        encoded = val.encode('utf-8')
        return ModelSerializationUtils.serialize_int(len(encoded)) + encoded

    @staticmethod
    def deserialize_str(data: bytes) -> str:
        length = ModelSerializationUtils.deserialize_int(data[:STR_LEN_BITS])
        return data[STR_LEN_BITS:length + STR_LEN_BITS].decode('utf-8')
