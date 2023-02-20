# main.py
# in chat.wire.client

from chat.common.client.events import main as client_main
from chat.common.config import Config
from chat.common.models import (
    CreateAccountRequest,
    CreateAccountResponse,
    DeleteAccountRequest,
    DeleteAccountResponse,
    DeliverUndeliveredMessagesRequest,
    DeliverUndeliveredMessagesResponse,
    ListAccountsRequest,
    ListAccountsResponse,
    LogInAccountRequest,
    LogInAccountResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from chat.common.operations import Opcode
from typing import Optional

import socket


def entry(**kwargs):
    # with ..
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((Config.HOST, Config.PORT))
    kwargs['s'] = s
    return kwargs


def request(opcode: Opcode,
            s: socket.socket = None,
            username: Optional[str] = None,
            message: Optional[str] = None,
            recipient_username: Optional[str] = None,
            sender_username: Optional[str] = None,
            **kwargs):
    object = None
    match opcode:
        case Opcode.LOGIN_ACCOUNT:
            object = LogInAccountRequest(username=username)
        case Opcode.CREATE_ACCOUNT:
            object = CreateAccountRequest(username=username)
        case Opcode.LIST_ACCOUNTS:
            object = ListAccountsRequest()
        case Opcode.SEND_MESSAGE:
            object = SendMessageRequest(
                message=message,
                recipient_username=recipient_username,
                sender_username=sender_username,
            )
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            object = DeliverUndeliveredMessagesRequest(username=username)
        case Opcode.DELETE_ACCOUNT:
            object = DeleteAccountRequest(username=username)

    request = object.serialize()
    s.sendall(request)
    response = s.recv(1024)

    match opcode:
        case Opcode.LOGIN_ACCOUNT:
            return LogInAccountResponse.deserialize(response)
        case Opcode.CREATE_ACCOUNT:
            return CreateAccountResponse.deserialize(response)
        case Opcode.LIST_ACCOUNTS:
            return ListAccountsResponse.deserialize(response)
        case Opcode.SEND_MESSAGE:
            return SendMessageResponse.deserialize(response)
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            return DeliverUndeliveredMessagesResponse.deserialize(response)
        case Opcode.DELETE_ACCOUNT:
            return DeleteAccountResponse.deserialize(response)


def handler(err: Exception, s: Optional[socket.socket] = None, **kwargs):
    if s is not None:
        s.shutdown()
        s.close()
    raise err


if __name__ == '__main__':
    client_main(entry=entry,
                request=request,
                handler=handler)
