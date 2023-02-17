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
            *args,
            channel: grpc.Channel = None,
            **kwargs):
    stub = proto_pb2_grpc.ChatStub(channel)

    if opcode == Opcode.LOGIN_ACCOUNT:
        request = proto_pb2.LogInAccountRequest(username=args[0])
        response = stub.LogInAccount(request)
    elif opcode == Opcode.CREATE_ACCOUNT:
        request = proto_pb2.CreateAccountRequest(username=args[0])
        response = stub.CreateAccount(request)
    elif opcode == Opcode.LIST_ACCOUNTS:
        request = proto_pb2.ListAccountsRequest()
        response = stub.ListAccounts(request)
    elif opcode == Opcode.SEND_MESSAGE:
        request = proto_pb2.SendMessageRequest(message=args[0],
                                               recipient_username=args[1],
                                               sender_username=args[2])
        response = stub.SendMessage(request)
    elif opcode == Opcode.DELIVER_UNDELIVERED_MESSAGES:
        request = proto_pb2.DeliverUndeliveredMessagesRequest(username=args[0])
        response = stub.DeliverUndeliveredMessages(request)
    elif opcode == Opcode.DELETE_ACCOUNT:
        request = proto_pb2.DeleteAccountRequest(username=args[0])
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
