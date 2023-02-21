# main.py
# in chat.grpc.client

from chat.common.client.events import main as client_main
from chat.common.config import Config
from chat.common.models import (
    CreateAccountResponse,
    DeleteAccountResponse,
    DeliverUndeliveredMessagesResponse,
    ListAccountsResponse,
    LogInAccountResponse,
    SendMessageResponse,
)
from chat.common.operations import Opcode
from typing import Optional

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


def entry(**kwargs):
    channel = grpc.insecure_channel(Config.HOST + ':' + str(Config.PORT))
    kwargs['channel'] = channel
    return kwargs


def request(opcode: Opcode, channel: grpc.Channel = None, **kwargs):
    stub = proto_pb2_grpc.ChatStub(channel)

    match opcode:
        case Opcode.LOGIN_ACCOUNT:
            req = proto_pb2.LogInAccountRequest(
                username=kwargs.get('username', None))
            res = stub.LogInAccount(req)
            response = LogInAccountResponse.from_grpc_model(res)
        case Opcode.CREATE_ACCOUNT:
            req = proto_pb2.CreateAccountRequest(
                username=kwargs.get('username', None))
            res = stub.CreateAccount(req)
            response = CreateAccountResponse.from_grpc_model(res)
        case Opcode.LIST_ACCOUNTS:
            req = proto_pb2.ListAccountsRequest()
            res = stub.ListAccounts(req)
            response = ListAccountsResponse.from_grpc_model(res)
        case Opcode.SEND_MESSAGE:
            req = proto_pb2.SendMessageRequest(
                message=kwargs.get('message', None),
                recipient_username=kwargs.get('recipient_username', None),
                sender_username=kwargs.get('sender_username', None))
            res = stub.SendMessage(req)
            response = SendMessageResponse.from_grpc_model(res)
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            req = proto_pb2.DeliverUndeliveredMessagesRequest(
                username=kwargs.get('username', None))
            res = stub.DeliverUndeliveredMessages(req)
            response = DeliverUndeliveredMessagesResponse.from_grpc_model(res)
        case Opcode.DELETE_ACCOUNT:
            req = proto_pb2.DeleteAccountRequest(
                username=kwargs.get('username', None))
            res = stub.DeleteAccount(req)
            response = DeleteAccountResponse.from_grpc_model(res)

    return response


def handler(err: Exception,
            channel: Optional[grpc.Channel] = None,
            **kwargs):
    if channel is not None:
        channel.close()
    raise err


if __name__ == '__main__':
    client_main(entry=entry,
                request=request,
                handler=handler)
