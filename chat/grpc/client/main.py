# main.py
# in chat.grpc.client

from chat.common.args import parse_client_args as parse_args
from chat.common.client.events import main as client_main
from chat.common.client.shiny.events import main as shiny_client_main
from chat.common.config import Config
from chat.common.models import (
    AcknowledgeMessagesResponse,
    CreateAccountResponse,
    DeleteAccountResponse,
    DeliverUndeliveredMessagesResponse,
    ListAccountsResponse,
    LogInAccountResponse,
    LogOutAccountResponse,
    SendMessageResponse,
)
from chat.common.operations import Opcode
from typing import Optional

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


def entry(host=Config.ADDRESSES[0][0], port=Config.ADDRESSES[0][1], **kwargs):
    """Establish a connection to the server.
    """
    channel = grpc.insecure_channel(f'{host!s}:{port!s}')
    kwargs['channel'] = channel
    return kwargs


def request(opcode: Opcode,
            channel: grpc.Channel = None,
            username: Optional[str] = None,
            text_wildcard: Optional[str] = None,
            message: Optional[str] = None,
            recipient_username: Optional[str] = None,
            sender_username: Optional[str] = None,
            logged_in: Optional[bool] = None,
            messages: Optional[list] = None,
            **kwargs):
    """Send a request to the server.
    """
    stub = proto_pb2_grpc.ChatStub(channel)

    match opcode:
        case Opcode.LOG_IN_ACCOUNT:
            req = proto_pb2.LogInAccountRequest(username=username)
            res = stub.LogInAccount(req)
            response = LogInAccountResponse.from_grpc_model(res)
        case Opcode.CREATE_ACCOUNT:
            req = proto_pb2.CreateAccountRequest(username=username)
            res = stub.CreateAccount(req)
            response = CreateAccountResponse.from_grpc_model(res)
        case Opcode.LIST_ACCOUNTS:
            req = proto_pb2.ListAccountsRequest(text_wildcard=text_wildcard)
            res = stub.ListAccounts(req)
            response = ListAccountsResponse.from_grpc_model(res)
        case Opcode.SEND_MESSAGE:
            req = proto_pb2.SendMessageRequest(
                message=message,
                recipient_username=recipient_username,
                sender_username=sender_username)
            res = stub.SendMessage(req)
            response = SendMessageResponse.from_grpc_model(res)
        case Opcode.DELIVER_UNDELIVERED_MESSAGES:
            req = proto_pb2.DeliverUndeliveredMessagesRequest(
                logged_in=logged_in,
                username=username)
            res = stub.DeliverUndeliveredMessages(req)
            response = DeliverUndeliveredMessagesResponse.from_grpc_model(res)
        case Opcode.DELETE_ACCOUNT:
            req = proto_pb2.DeleteAccountRequest(
                username=username)
            res = stub.DeleteAccount(req)
            response = DeleteAccountResponse.from_grpc_model(res)
        case Opcode.LOG_OUT_ACCOUNT:
            req = proto_pb2.LogOutAccountRequest(
                username=username)
            res = stub.LogOutAccount(req)
            response = LogOutAccountResponse.from_grpc_model(res)
        case Opcode.ACKNOWLEDGE_MESSAGES:
            req = proto_pb2.AcknowledgeMessagesRequest(
                messages=[proto_pb2.Message(
                              message=message
                              .get_message(),
                              recipient_logged_in=message
                              .get_recipient_logged_in(),
                              recipient_username=message
                              .get_recipient_username(),
                              sender_username=message
                              .get_sender_username(),
                              time=message
                              .get_time(),
                              delivered=message
                              .get_delivered())
                          for message in messages])
            res = stub.AcknowledgeMessages(req)
            response = AcknowledgeMessagesResponse.from_grpc_model(res)

    return response


def handler(err: Exception,
            channel: Optional[grpc.Channel] = None,
            **kwargs):
    """Handle errors (i.e. close the channel).
    """
    if channel is not None:
        channel.close()
    raise err


def main(host=Config.ADDRESSES[0][0], port=Config.ADDRESSES[0][1], shiny=False, **kwargs):
    """Start the client.
    """
    if shiny:
        shiny_client_main(entry=entry,
                          request=request,
                          handler=handler,
                          host=host,
                          port=port,
                          **kwargs)
    else:
        client_main(entry=entry,
                    request=request,
                    handler=handler,
                    host=host,
                    port=port,
                    **kwargs)


if __name__ == '__main__':
    main(**parse_args().__dict__)
