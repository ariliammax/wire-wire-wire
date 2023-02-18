# events.py
# in chat.common.server

from chat.common.models import Account, Message
from chat.common.server.database import Database


class Events:
    @staticmethod
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
        return " "

    @staticmethod
    def list_accounts():
        return ",".join(f'{acc._username!s} '
                        f'({"in" if not acc._logged_in else ""!s}'
                        f'active)'
                        for _, acc in
                        Database.get_accounts().items())

    @staticmethod
    def send_message(message: str,
                     recipient_username: str,
                     sender_username: str):
        message = (Message()
                   .set_delivered(False)
                   .set_message(message)
                   .set_recipient_username(recipient_username)
                   .set_sender_username(sender_username)
                   .set_time(0))
        Database.upsert_message(message)
        return " "

    @staticmethod
    def deliver_undelivered_messages(username: str):
        messages = []
        account = Database._accounts[username]
        messages_by_sender = Database.get_messages(account)
        if (not messages_by_sender):
            return "No new messages!"
        else:
            for sender, message_list in messages_by_sender.items():
                messages.append(f"{sender}\n")
                for message in message_list:
                    message.set_delivered(True)
                    messages.append(f"> {message._message}\n")
            return "".join(messages)

    @staticmethod
    def delete_account(username: str):
        Database.delete_account(Account()
                                .set_username(username))
        return " "

    @staticmethod
    def account_logout(username: str):
        if username in Database._accounts:
            account = (Account()
                       .set_username(username)
                       .set_logged_in(False))
            Database.upsert_account(account)
