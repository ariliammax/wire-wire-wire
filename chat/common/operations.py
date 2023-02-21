# operations.py
# in chat.common

from enum import Enum


# OP CODES
class Opcode(Enum):
    LOG_IN_ACCOUNT = 0
    CREATE_ACCOUNT = 1
    LIST_ACCOUNTS = 2
    SEND_MESSAGE = 3
    DELIVER_UNDELIVERED_MESSAGES = 4
    DELETE_ACCOUNT = 5
    LOG_OUT_ACCOUNT = 6
    ACKNOWLEDGE_MESSAGES = 7
