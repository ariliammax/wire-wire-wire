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
            messages.append(message)
            messages.sort(key=lambda m: m.get_time())
            cls._messages[username] = messages

    @classmethod
    def get_messages(cls, recipient: Optional[Account] = None):
        messages = {}
        with cls.messages_lock:
            messages = {k: v for k, v in cls._messages.items() if
                        recipient is not None and
                        k == recipient.get_username()}
        return messages

    @classmethod
    def delete_account(cls, account: Account):
        username = account.get_username()
        with cls.accounts_lock:
            cls._accounts.pop(username)
        with cls.messages_lock:
            cls._messages.pop(username)
