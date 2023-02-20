# events.py
# in chat.common.server

from chat.common.models import (
    Account,
    CreateAccountResponse,
    DeleteAccountResponse,
    DeliverUndeliveredMessagesResponse,
    ListAccountsResponse,
    LogInAccountResponse,
    Message,
    SendMessageResponse,
)
from chat.common.operations import Opcode
from chat.common.server.database import Database


# These are all kwargs accepting, so we can attach to `Opcode`s in the wire
# protocol so it's a clean lil pipe from the deserialization, or we can call
# it on-the-nose from gRPC.
class Events:

    @staticmethod
    def login_account(username: str, **kwargs):
        # set state (just `username`)
        username = username
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if Database.has_account(account):
            pass
            # response = ' '
            #  (f'ERROR: Account {username!s} already '
            #   f'exists... logging in!')

        Database.upsert_account(account)
        return LogInAccountResponse()

    @staticmethod
    def create_account(username: str, **kwargs):
        # set state (just `username`)
        username = username
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if Database.has_account(account):
            pass
            # response = ' '
            #  (f'ERROR: Account {username!s} already '
            #   f'exists... logging in!')

        Database.upsert_account(account)
        return CreateAccountResponse()

    @staticmethod
    def list_accounts(**kwargs):
        return ListAccountsResponse(
            accounts=[acc for _, acc in Database.get_accounts().items()])

    @staticmethod
    def send_message(message: str,
                     recipient_username: str,
                     sender_username: str,
                     **kwargs):
        message = (Message()
                   .set_delivered(False)
                   .set_message(message)
                   .set_recipient_username(recipient_username)
                   .set_sender_username(sender_username)
                   .set_time(0))
        Database.upsert_message(message)
        return SendMessageResponse()

    @staticmethod
    def deliver_undelivered_messages(username: str, **kwargs):
        messages = []
        account = Database._accounts[username]
        messages_by_sender = Database.get_messages(account)
        if (not messages_by_sender):
            return DeliverUndeliveredMessagesResponse(
                error='No new messages!')
        else:
            messages = sum([msg for _, msg in messages_by_sender.items()],
                           start=[])
            return DeliverUndeliveredMessagesResponse(messages=messages)

    @staticmethod
    def delete_account(username: str, **kwargs):
        Database.delete_account(Account()
                                .set_username(username))
        return DeleteAccountResponse()

    @staticmethod
    def account_logout(username: str, **kwargs):
        if username in Database._accounts:
            account = (Account()
                       .set_username(username)
                       .set_logged_in(False))
            Database.upsert_account(account)


EventsRouter = {Opcode.LOGIN_ACCOUNT:
                Events.login_account,
                Opcode.CREATE_ACCOUNT:
                Events.create_account,
                Opcode.LIST_ACCOUNTS:
                Events.list_accounts,
                Opcode.SEND_MESSAGE:
                Events.send_message,
                Opcode.DELIVER_UNDELIVERED_MESSAGES:
                Events.deliver_undelivered_messages,
                Opcode.DELETE_ACCOUNT:
                Events.delete_account}
