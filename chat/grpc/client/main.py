# main.py
# in chat.grpc.client

from chat.common.client.events import main as client_main
from chat.common.config import Config
from chat.common.operations import Opcode
from typing import Optional

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


def entry(**kwargs):
    channel = grpc.insecure_channel(Config.HOST + ':' + str(Config.PORT))
    kwargs['channel'] = channel
    return kwargs


def request(opcode: Opcode,
            channel: grpc.Channel = None,
            **kwargs):
    stub = proto_pb2_grpc.ChatStub(channel)

    match opcode:
        case Opcode.LOGIN_ACCOUNT:
            request = proto_pb2.LogInAccountRequest(
                username=kwargs.get('username', None))
            response = stub.LogInAccount(request)
        case Opcode.CREATE_ACCOUNT:
            request = proto_pb2.CreateAccountRequest(
                username=kwargs.get('username', None))
            response = stub.CreateAccount(request)
        case Opcode.LIST_ACCOUNTS:
            request = proto_pb2.ListAccountsRequest()
            response = stub.ListAccounts(request)
        case Opcode.SEND_MESSAGE:
            request = proto_pb2.SendMessageRequest(
                message=kwargs.get('message', None),
                recipient_username=kwargs.get('recipient_username', None),
                sender_username=kwargs.get('sender_username', None))
            response = stub.SendMessage(request)
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            request = proto_pb2.DeliverUndeliveredMessagesRequest(
                username=kwargs.get('username', None))
            response = stub.DeliverUndeliveredMessages(request)
        case Opcode.DELETE_ACCOUNT:
            request = proto_pb2.DeleteAccountRequest(
                username=kwargs.get('username', None))
            response = stub.DeleteAccount(request)

    return response.error


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
