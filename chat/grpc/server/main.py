# main.py
# in chat.grpc.server

from chat.common.config import Config
from chat.common.server.events import Events
from concurrent import futures

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


class ChatServicer(proto_pb2_grpc.ChatServicer):
    def LogInAccount(self, request, context):
        response = Events.login_account(username=request.username)
        return proto_pb2.LogInAccountResponse(error=response.get_error())

    def CreateAccount(self, request, context):
        response = Events.create_account(username=request.username)
        return proto_pb2.CreateAccountResponse(error=response.get_error())

    def ListAccounts(self, request, context):
        response = Events.list_accounts()
        return proto_pb2.ListAccountsResponse(
            error=response.get_error(),
            accounts=[proto_pb2.Account(username=acc.get_username())
                      for acc in response.get_accounts()])

    def SendMessage(self, request, context):
        response = Events.send_message(
            message=request.message,
            recipient_username=request.recipient_username,
            sender_username=request.sender_username)
        return proto_pb2.SendMessageResponse(error=response.get_error())

    def DeliverUndeliveredMessages(self, request, context):
        response = Events.deliver_undelivered_messages(
            username=request.username)
        return proto_pb2.DeliverUndeliveredMessagesResponse(
            error=response.get_error(),
            messages=[proto_pb2.Message(sender_username=msg
                                        .get_sender_username(),
                                        recipient_username=msg
                                        .get_recipient_username(),
                                        message=msg.get_message())
                      for msg in response.get_messages()])

    def DeleteAccount(self, request, context):
        response = Events.delete_account(username=request.username)
        return proto_pb2.DeleteAccountResponse(error=response.get_error())


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=Config
                                                    .MAX_WORKERS))
    proto_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port(f'[::]:{Config.PORT!s}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
