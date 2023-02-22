# events.py
# in chat.common.server

from chat.common.models import (
    Account,
    AcknowledgeMessagesResponse,
    CreateAccountResponse,
    DeleteAccountResponse,
    DeliverUndeliveredMessagesResponse,
    ListAccountsResponse,
    LogInAccountResponse,
    LogOutAccountResponse,
    Message,
    SendMessageResponse,
)
from chat.common.operations import Opcode
from chat.common.server.database import Database

import time


# These are all kwargs accepting, so we can attach to `Opcode`s in the wire
# protocol so it's a clean lil pipe from the deserialization, or we can call
# it on-the-nose from gRPC.
class Events:

    @staticmethod
    def log_in_account(username: str, **kwargs):
        # set state (just `username`)
        username = username
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if not Database.has_account(account):
            return LogInAccountResponse(error='This account does not exist.')
        Database.upsert_account(account)
        return LogInAccountResponse(error='')

    @staticmethod
    def create_account(username: str, **kwargs):
        # set state (just `username`)
        username = username
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if Database.has_account(account):
            return CreateAccountResponse(error='This account already exists.')
        Database.upsert_account(account)
        return CreateAccountResponse(error='')

    @staticmethod
    def list_accounts(text_wildcard: str, **kwargs):
        return ListAccountsResponse(
            accounts=[account
                      for _, account in Database.get_accounts().items()
                      if text_wildcard in account.get_username()],
            error='')

    @staticmethod
    def send_message(message: str,
                     recipient_username: str,
                     sender_username: str,
                     **kwargs):
        recipient_account = (Account()
                             .set_username(recipient_username))
        if not Database.has_account(recipient_account):
            return SendMessageResponse(
                error='Recipient account does not exist.')
        message = (Message()
                   .set_delivered(False)
                   .set_message(message)
                   .set_recipient_username(recipient_username)
                   .set_sender_username(sender_username)
                   .set_time(int(time.time())))
        Database.upsert_message(message)
        return SendMessageResponse(error='')

    @staticmethod
    def deliver_undelivered_messages(username: str, **kwargs):
        messages = []
        account = Database.get_accounts()[username]
        messages = Database.get_messages(account)
        if not messages:
            return DeliverUndeliveredMessagesResponse(
                error='No new messages!',
                messages=[])
        return DeliverUndeliveredMessagesResponse(error='',
                                                  messages=messages)

    @staticmethod
    def delete_account(username: str, **kwargs):
        Database.delete_account(Account()
                                .set_username(username))
        return DeleteAccountResponse(error='')

    @staticmethod
    def log_out_account(username: str, **kwargs):
        if username not in Database._accounts:
            return LogOutAccountResponse(error='This account does not exist.')
        account = (Account()
                   .set_username(username)
                   .set_logged_in(False))
        Database.upsert_account(account)
        return LogOutAccountResponse(error='')

    @staticmethod
    def acknowledge_messages(messages: list, **kwargs):
        for message in messages:
            message.set_delivered(True)
            Database.upsert_message(message)
        return AcknowledgeMessagesResponse(error='')


EventsRouter = {Opcode.LOG_IN_ACCOUNT:
                Events.log_in_account,
                Opcode.CREATE_ACCOUNT:
                Events.create_account,
                Opcode.LIST_ACCOUNTS:
                Events.list_accounts,
                Opcode.SEND_MESSAGE:
                Events.send_message,
                Opcode.DELIVER_UNDELIVERED_MESSAGES:
                Events.deliver_undelivered_messages,
                Opcode.DELETE_ACCOUNT:
                Events.delete_account,
                Opcode.LOG_OUT_ACCOUNT:
                Events.log_out_account,
                Opcode.ACKNOWLEDGE_MESSAGES:
                Events.acknowledge_messages}
