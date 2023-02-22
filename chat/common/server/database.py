# database.py
# in chat.common.server

from chat.common.models import Account, Message
from threading import Lock
from typing import Dict, Optional


class Database(object):

    # key is username
    _accounts: Dict[str, Account] = {}
    accounts_lock: Lock = Lock()

    # key is recipient_username
    _messages: Dict[str, Message] = {}
    messages_lock: Lock = Lock()

    @classmethod
    def upsert_account(cls, account: Account):
        with cls.accounts_lock:
            cls._accounts[account.get_username()] = account

    @classmethod
    def get_accounts(cls):
        accounts = {}
        with cls.accounts_lock:
            accounts = {k: v for k, v in cls._accounts.items()}
        return accounts

    @classmethod
    def get_account_logged_in(cls, account: Account):
        logged_in = None
        with cls.accounts_lock:
            username = account.get_username()
            if username in cls._accounts:
                logged_in = cls._accounts[username].get_logged_in()
        return logged_in

    @classmethod
    def has_account(cls, account: Account):
        ret = False
        with cls.accounts_lock:
            ret = account.get_username() in cls._accounts
        return ret

    @classmethod
    def upsert_message(cls, message: Message):
        with cls.messages_lock:
            username = message.get_recipient_username()
            if username not in cls._messages:
                cls._messages[username] = []
            messages = cls._messages[username]
            if message.get_delivered():
                message.set_delivered(False)
                idx = None
                for i, msg in enumerate(messages):
                    if msg == message:
                        idx = i
                        break
                if idx is not None:
                    messages[idx].set_delivered(True)
                else:
                    message.set_delivered(True)
                    messages.append(message)
            else:
                messages.append(message)
            messages.sort(key=lambda m: m.get_time())
            cls._messages[username] = messages

    @classmethod
    def get_messages(cls, account: Account, logged_in: bool):
        recipient_messages = []
        with cls.messages_lock:
            recipient_username = account.get_username()
            if recipient_username not in cls._messages:
                return []
            messages = cls._messages[recipient_username]
            recipient_messages = [msg for msg in messages
                                  if not msg.get_delivered() and
                                    (not logged_in or
                                     msg.get_recipient_logged_in())]
        return recipient_messages

    @classmethod
    def delete_account(cls, account: Account):
        username = account.get_username()
        with cls.accounts_lock:
            cls._accounts.pop(username, None)
        with cls.messages_lock:
            cls._messages.pop(username, None)
