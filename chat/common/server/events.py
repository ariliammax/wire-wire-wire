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


class Events:
    """All of the operations/events that the server can do, given the object
        models. I.e. the database actions and creating the responses.
        These are all kwargs accepting, so we can attach to `Opcode`s in the
        wire protocol so it's a clean lil pipe from the deserialization, or we
        can call it on-the-nose from gRPC.
    """

    @staticmethod
    def startup(machine_id=0):
        Database.startup(machine_id=machine_id)

    @staticmethod
    def log_in_account(username: str, **kwargs):
        """Logs an account in. Sends error if doesn't exist.
        """
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if not Database.has_account(account):
            return LogInAccountResponse(error='This account does not exist.')
        Database.upsert_account(account)
        return LogInAccountResponse(error='')

    @staticmethod
    def create_account(username: str, **kwargs):
        """Creates an account. Sends error if already exists.
        """
        account = (Account()
                   .set_username(username)
                   .set_logged_in(True))
        if Database.has_account(account):
            return CreateAccountResponse(error='This account already exists.')
        Database.upsert_account(account)
        return CreateAccountResponse(error='')

    @staticmethod
    def list_accounts(text_wildcard: str, **kwargs):
        """Lists all the accounts, subject to some token. Implicitly places
            a wildcard on both the head and tail.
        """
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
        """Adds a message to the database (i.e. sent from the sender's
            perspective). Sends error if recipient doesn't exist.
        """
        recipient_account = (Account()
                             .set_username(recipient_username))
        if not Database.has_account(recipient_account):
            return SendMessageResponse(
                error='Recipient account does not exist.')
        logged_in = Database.get_account_logged_in(recipient_account)
        message = (Message()
                   .set_delivered(False)
                   .set_message(message)
                   .set_recipient_logged_in(logged_in)
                   .set_recipient_username(recipient_username)
                   .set_sender_username(sender_username)
                   .set_time(int(time.time())))
        Database.upsert_message(message)
        return SendMessageResponse(error='')

    @staticmethod
    def deliver_undelivered_messages(logged_in: bool, username: str, **kwargs):
        """Delivers any undelivered messages to the recipient. Sends error
            if there aren't any.
        """
        messages = []
        account = Database.get_accounts()[username]
        messages = Database.get_messages(account, logged_in)
        if not messages:
            return DeliverUndeliveredMessagesResponse(
                error='No new messages!',
                messages=[])
        return DeliverUndeliveredMessagesResponse(error='',
                                                  messages=messages)

    @staticmethod
    def delete_account(username: str, **kwargs):
        """Deletes an account.
        """
        account = (Account()
                   .set_username(username))
        if Database.has_account(account):
            Database.delete_account(account)
            return DeleteAccountResponse(error='')
        else:
            return DeleteAccountResponse(error='This account does not exist.')

    @staticmethod
    def log_out_account(username: str, **kwargs):
        """Logs out an account. Sends error if doesn't exist (deleted).
        """
        account = (Account()
                   .set_username(username)
                   .set_logged_in(False))
        if not Database.has_account(account):
            return DeleteAccountResponse(error='This account does not exist.')
        else:
            Database.upsert_account(account)
            return LogOutAccountResponse(error='')

    @staticmethod
    def acknowledge_messages(messages: list, **kwargs):
        """Acknowledges the receiving of messages, so it's nice and
            transactional. Won't be marked delivered until now.
        """
        for message in messages:
            message.set_delivered(True)
            Database.upsert_message(message)
        return AcknowledgeMessagesResponse(error='')


# A nice map of `Opcode`s to `Events`.
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
