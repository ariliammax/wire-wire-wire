# operations.py
# in chat.common

# from chat.common.util import interface, class_from_proto
from enum import Enum
from chat.common.models import Account, Message  # noqa
from chat.common.server.database import Database


# OP CODES
class Opcode(Enum):
    LOGIN_ACCOUNT = 0
    CREATE_ACCOUNT = 1
    LIST_ACCOUNTS = 2
    SEND_MESSAGE = 3
    DELIVER_UNDELIVERED_MESSAGES = 4
    DELETE_ACCOUNT = 5


class Operations():
    def create_account(username: str):
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

    def list_accounts():
        return ",".join(f'{acc._username!s} '
                        f'({"in" if not acc._logged_in else ""!s}'
                        f'active)'
                        for _, acc in
                        Database.get_accounts().items())

    def send_message(msg: str, recipient: str, sender: str):
        message = (Message()
                    .set_delivered(False)
                    .set_message(msg)
                    .set_recipient_username(recipient)
                    .set_sender_username(sender)
                    .set_time(0))
        Database.upsert_message(message)

    def deliver_undelivered_messages(username: str):
        messages = []
        account = Database._accounts[username]
        messages_by_sender = Database.get_messages(account)
        print(messages_by_sender)
        if (not messages_by_sender):
            return "No new messages!"
        else:
            for sender, message_list in messages_by_sender.items():
                messages.append(f"{sender}\n")
                for message in message_list:
                    message.set_delivered(True)
                    messages.append(f"> {message._message}\n")
            return "".join(messages)

    def delete_account(username: str):
        Database.delete_account(Account()
                                .set_username(username))


