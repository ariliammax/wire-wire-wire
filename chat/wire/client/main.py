# main.py
# in chat.wire.client

from chat.common.client.events import main as client_main
from chat.common.config import Config
from chat.common.models import (
    AcknowledgeMessagesRequest,
    AcknowledgeMessagesResponse,
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
    LogOutAccountRequest,
    LogOutAccountResponse,
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
            text_wildcard: Optional[str] = None,
            message: Optional[str] = None,
            recipient_username: Optional[str] = None,
            sender_username: Optional[str] = None,
            messages: Optional[list] = None,
            **kwargs):
    obj = None
    match opcode:
        case Opcode.LOG_IN_ACCOUNT:
            obj = LogInAccountRequest(username=username)
        case Opcode.CREATE_ACCOUNT:
            obj = CreateAccountRequest(username=username)
        case Opcode.LIST_ACCOUNTS:
            obj = ListAccountsRequest(text_wildcard=text_wildcard)
        case Opcode.SEND_MESSAGE:
            obj = SendMessageRequest(
                message=message,
                recipient_username=recipient_username,
                sender_username=sender_username,
            )
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            obj = DeliverUndeliveredMessagesRequest(username=username)
        case Opcode.DELETE_ACCOUNT:
            obj = DeleteAccountRequest(username=username)
        case Opcode.LOG_OUT_ACCOUNT:
            obj = LogOutAccountRequest(username=username)
        case Opcode.ACKNOWLEDGE_MESSAGES:
            obj = AcknowledgeMessagesRequest(messages=messages)

    request = obj.serialize()
    s.sendall(request)
    response = s.recv(1024)

    match opcode:
        case Opcode.LOG_IN_ACCOUNT:
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
        case Opcode.LOG_OUT_ACCOUNT:
            return LogOutAccountResponse.deserialize(response)
        case Opcode.ACKNOWLEDGE_MESSAGES:
            return AcknowledgeMessagesResponse.deserialize(response)


def handler(err: Exception, s: Optional[socket.socket] = None, **kwargs):
    if s is not None:
        s.shutdown()
        s.close()
    raise err


if __name__ == '__main__':
    client_main(entry=entry,
                request=request,
                handler=handler)
