# main.py
# in chat.grpc.server

from chat.common.args import parse_server_args as parse_args
from chat.common.config import Config
from chat.common.models import Message
from chat.common.server.events import Events
from concurrent import futures

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


class ChatServicer(proto_pb2_grpc.ChatServicer):
    """Actually pass all of the endpoints to `Events`.
        There's probably a nice way to automate all of this, but I can't be
        bothered to yet.
    """

    def LogInAccount(self, request, context):
        response = Events.log_in_account(username=request.username)
        return proto_pb2.LogInAccountResponse(error=response.get_error())

    def CreateAccount(self, request, context):
        response = Events.create_account(username=request.username)
        return proto_pb2.CreateAccountResponse(error=response.get_error())

    def ListAccounts(self, request, context):
        response = Events.list_accounts(text_wildcard=request.text_wildcard)
        return proto_pb2.ListAccountsResponse(
            error=response.get_error(),
            accounts=[proto_pb2.Account(logged_in=acc.get_logged_in(),
                                        username=acc.get_username())
                      for acc in response.get_accounts()])

    def SendMessage(self, request, context):
        response = Events.send_message(
            message=request.message,
            recipient_username=request.recipient_username,
            sender_username=request.sender_username)
        return proto_pb2.SendMessageResponse(error=response.get_error())

    def DeliverUndeliveredMessages(self, request, context):
        response = Events.deliver_undelivered_messages(
            logged_in=request.logged_in,
            username=request.username)
        return proto_pb2.DeliverUndeliveredMessagesResponse(
            error=response.get_error(),
            messages=[proto_pb2.Message(message=msg
                                        .get_message(),
                                        recipient_logged_in=msg
                                        .get_recipient_logged_in(),
                                        recipient_username=msg
                                        .get_recipient_username(),
                                        sender_username=msg
                                        .get_sender_username(),
                                        time=msg
                                        .get_time(),
                                        delivered=msg
                                        .get_delivered())
                      for msg in response.get_messages()])

    def AcknowledgeMessages(self, request, context):
        response = Events.acknowledge_messages(
            messages=[Message.from_grpc_model(msg)
                      for msg in request.messages])
        return proto_pb2.AcknowledgeMessagesResponse(
            error=response.get_error())

    def DeleteAccount(self, request, context):
        response = Events.delete_account(username=request.username)
        return proto_pb2.DeleteAccountResponse(error=response.get_error())

    def LogOutAccount(self, request, context):
        response = Events.log_out_account(username=request.username)
        return proto_pb2.LogOutAccountResponse(error=response.get_error())


def main(port=Config.PORT, **kwargs):
    """Start a server and keep on listening.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=Config
                                                    .MAX_WORKERS))
    proto_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port(f'[::]:{port!s}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main(**parse_args().__dict__)
