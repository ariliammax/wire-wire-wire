# main.py
# in chat.grpc.server

from chat.common.config import Config
from chat.common.serve.events import Events
from concurrent import futures

import grpc
import chat.grpc.grpcio.proto_pb2 as proto_pb2
import chat.grpc.grpcio.proto_pb2_grpc as proto_pb2_grpc


class ChatServicer(proto_pb2_grpc.ChatServicer):
    def LogInAccount(self, request, context):
        error = Events.create_account(username=request.username)
        return proto_pb2.LogInAccountResponse(error=error)

    def CreateAccount(self, request, context):
        error = Events.create_account(username=request.username)
        return proto_pb2.CreateAccountResponse(error=error)

    def ListAccounts(self, request, context):
        error = Events.list_accounts()
        accounts = []
        return proto_pb2.ListAccountsResponse(error=error,
                                              accounts=accounts)

    def SendMessage(self, request, context):
        error = Events.send_message(message=request.message,
                                    recipient_username=request
                                    .recipient_username,
                                    sender_username=request.sender_username)
        return proto_pb2.SendMessageResponse(error=error)

    def DeliverUndeliveredMessages(self, request, context):
        error = Events.deliver_undelivered_messages(username=request.username)
        messages = []
        return proto_pb2.DeliverUndeliveredMessagesResponse(error=error,
                                                            messages=messages)

    def DeleteAccount(self, request, context):
        error = Events.delete_account(username=request.username)
        return proto_pb2.DeleteAccountResponse(error=error)


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=Config
                                                    .MAX_WORKERS))
    proto_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port(f'[::]:{Config.PORT!s}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
