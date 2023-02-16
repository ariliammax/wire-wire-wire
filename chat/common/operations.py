# operations.py
# in chat.common

from chat.common.util import interface, class_from_proto
from enum import Enum
from typing import Optional


## OP CODES
class Opcode(Enum):
    LOGIN_ACCOUNT = 0
    CREATE_ACCOUNT = 1
    LIST_ACCOUNTS = 2
    SEND_MESSAGE = 3
    DELIVER_UNDELIVERED_MESSAGES = 4
    DELETE_ACCOUNT = 5