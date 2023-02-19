# events.py
# in chat.common.server

from chat.common.models import Account, Message
from chat.common.operations import Opcode
from chat.common.server.database import Database


# These are all kwargs accepting, so we can attach to `Opcode`s in the wire
# protocol so it's a clean lil pipe from the deserialization, or we can call
# it on-the-nose from gRPC.
class Events:

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
        return ' '

    @staticmethod
    def list_accounts(**kwargs):
        return ','.join(f'{acc._username!s} '
                        f'({"in" if not acc._logged_in else ""!s}'
                        f'active)'
                        for _, acc in
                        Database.get_accounts().items())

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
        return ' '

    @staticmethod
    def deliver_undelivered_messages(username: str, **kwargs):
        messages = []
        account = Database._accounts[username]
        messages_by_sender = Database.get_messages(account)
        if (not messages_by_sender):
            return 'No new messages!'
        else:
            for sender, message_list in messages_by_sender.items():
                messages.append(f'{sender}\n')
                for message in message_list:
                    message.set_delivered(True)
                    messages.append(f'> {message._message}\n')
            return ''.join(messages)

    @staticmethod
    def delete_account(username: str, **kwargs):
        Database.delete_account(Account()
                                .set_username(username))
        return ' '

    @staticmethod
    def account_logout(username: str, **kwargs):
        if username in Database._accounts:
            account = (Account()
                       .set_username(username)
                       .set_logged_in(False))
            Database.upsert_account(account)


EventsRouter = {Opcode.CREATE_ACCOUNT:
                Events.create_account,
                Opcode.LIST_ACCOUNTS:
                Events.list_accounts,
                Opcode.SEND_MESSAGE:
                Events.send_message,
                Opcode.DELIVER_UNDELIVERED_MESSAGES:
                Events.deliver_undelivered_messages,
                Opcode.DELETE_ACCOUNT:
                Events.delete_account}
