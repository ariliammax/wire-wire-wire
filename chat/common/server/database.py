# database.py
# in chat.common.server

from chat.common.config import Config
from chat.common.models import Account, Message
from chat.common.models import BaseRequest, BaseResponse
from chat.common.serialization import SerializationUtils
from enum import Enum
from threading import Lock, Thread
from typing import Dict

import socket


class DatabaseOpcode(Enum):
    DELETE_ACCOUNT = 0
    DELETE_ALL = 1
    GET_ACCOUNT_LOGGED_IN = 3
    GET_ACCOUNTS = 2
    GET_MESSAGES = 4
    HAS_ACCOUNT = 5
    UPSERT_ACCOUNT = 6
    UPSERT_MESSAGE = 7

    SYNC_DATA = 8


class DatabaseRequests:
    DeleteAccount = BaseRequest.add_fields_with_opcode(
        account=Account,
        opcode=DatabaseOpcode.DELETE_ACCOUNT.value
    )
    DeleteAll = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.DELETE_ALL.value
    )
    GetAccountLoggedIn = BaseRequest.add_fields_with_opcode(
        account=Account,
        opcode=DatabaseOpcode.GET_ACCOUNT_LOGGED_IN.value
    )
    GetAccounts = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.GET_ACCOUNTS.value
    )
    GetMessages = BaseRequest.add_fields_with_opcode(
        account=Account,
        logged_in=bool,
        opcode=DatabaseOpcode.GET_MESSAGES.value
    )
    HasAccount = BaseRequest.add_fields_with_opcode(
        account=Account,
        opcode=DatabaseOpcode.HAS_ACCOUNT.value
    )
    UpsertAccount = BaseRequest.add_fields_with_opcode(
        account=Account,
        opcode=DatabaseOpcode.UPSERT_ACCOUNT.value
    )
    UpsertMessage = BaseRequest.add_fields_with_opcode(
        the_message=Message,  # if this is `message`, `get_message` goes too deep
        opcode=DatabaseOpcode.UPSERT_MESSAGE.value
    )

    SyncData = BaseRequest.add_fields_with_opcode(
        accounts=list,
        messages=list,
        fields_list_nested=dict(
            accounts=Account,
            messages=Message
        ),
        opcode=DatabaseOpcode.SYNC_DATA.value
    )


class DatabaseResponses:
    DeleteAccount = BaseResponse.add_fields_with_opcode(
        opcode=DatabaseOpcode.DELETE_ACCOUNT.value
    )
    DeleteAll = BaseResponse.add_fields_with_opcode(
        opcode=DatabaseOpcode.DELETE_ALL.value
    )
    GetAccountLoggedIn = BaseResponse.add_fields_with_opcode(
        logged_in=bool,
        opcode=DatabaseOpcode.GET_ACCOUNT_LOGGED_IN.value
    )
    GetAccounts = BaseResponse.add_fields_with_opcode(
        accounts=list,
        fields_list_nested=dict(accounts=Account),
        opcode=DatabaseOpcode.GET_ACCOUNTS.value
    )
    GetMessages = BaseResponse.add_fields_with_opcode(
        messages=list,
        fields_list_nested=dict(messages=Message),
        opcode=DatabaseOpcode.GET_MESSAGES.value
    )
    HasAccount = BaseResponse.add_fields_with_opcode(
        has_account=bool,
        opcode=DatabaseOpcode.HAS_ACCOUNT.value
    )
    UpsertAccount = BaseResponse.add_fields_with_opcode(
        opcode=DatabaseOpcode.UPSERT_ACCOUNT.value
    )
    UpsertMessage = BaseResponse.add_fields_with_opcode(
        opcode=DatabaseOpcode.UPSERT_MESSAGE.value
    )


class Database(object):
    """A `Database` for the chat programs.
    """

    # key is username
    _accounts: Dict[str, Account] = {}

    # key is recipient_username
    _messages: Dict[str, Message] = {}

    addresses = Config.ADDRESSES

    machines_down: list = [False, False, False]
    machine_id: int = None
    machine_lock: Lock = Lock()

    queue_sockets: dict = {}
    sync_sockets: dict = {}
    queue_connections: dict = {}
    sync_connections: dict = {}

    @classmethod
    def startup(cls, machine_id=0, addresses=Config.ADDRESSES):
        cls.addresses = addresses

        was_primarys = [None, None, None]
        with cls.machine_lock:
            cls.machine_id = machine_id

            try:
                with open(cls.accounts_file_name(), "rb") as file:
                    content = b''.join(file.readlines())
                    for account in cls.deserialize_accounts(content):
                        cls.local_upsert_account(account)
            except FileNotFoundError:
                pass
            except:
                # no content or some random deserialization error
                pass

            try:
                with open(cls.messages_file_name(), "rb") as file:
                    content = b''.join(file.readlines())
                    for message in cls.deserialize_messages(content):
                        cls.local_upsert_message(message)
            except FileNotFoundError:
                pass
            except:
                # no content or some random deserialization error
                pass

            try:
                with open(cls.primary_log_file_name(), "r") as file:
                    content = file.readlines()
                    was_primary = content[0] == "1"
                    was_primarys[cls.machine_id] = was_primary
            except FileNotFoundError:
                was_primary = False
                was_primarys[cls.machine_id] = was_primary

            host, port = cls.addresses[machine_id]

            port += 1 # original + 1
            queue_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            queue_socket.bind((host, port))
            queue_socket.settimeout(None) # infinite
            queue_socket.listen()

            port += 1 # original + 2
            sync_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sync_socket.bind((host, port))
            sync_socket.settimeout(None) # infinite
            sync_socket.listen()

        def connect_to_queue(other_machine_id):
            other_host, other_port = cls.addresses[other_machine_id]
            other_port += 1
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(Config.TIMEOUT_QUEUE)
                    s.connect((other_host, other_port))
                    s.sendall(int.to_bytes(machine_id, 1, byteorder='little'))
                    with cls.machine_lock:
                        cls.queue_sockets[other_machine_id] = s
                    break
                except:
                    pass

        def connect_to_sync(other_machine_id):
            other_host, other_port = cls.addresses[other_machine_id]
            other_port += 2
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(Config.TIMEOUT_SYNC)
                    s.connect((other_host, other_port))
                    i = machine_id * 2 + int(was_primarys[cls.machine_id])
                    s.sendall(int.to_bytes(i, 1, byteorder='little'))
                    with cls.machine_lock:
                        cls.sync_sockets[other_machine_id] = s
                    break
                except:
                    pass

        def accept_on_queue():
            while True:
                try:
                    connection, _ = queue_socket.accept()
                    request = connection.recv(1024)
                    if len(request) == 0:
                        continue
                    other_machine_id = int.from_bytes(request, byteorder='little')
                    with cls.machine_lock:
                        cls.queue_connections[other_machine_id] = connection
                    break
                except:
                    pass

        def accept_on_sync():
            while True:
                try:
                    connection, _ = sync_socket.accept()
                    request = connection.recv(1024)
                    if len(request) == 0:
                        continue
                    i = int.from_bytes(request, byteorder='little')
                    other_machine_id = i // 2
                    other_was_primary = i % 2 == 1
                    with cls.machine_lock:
                        was_primarys[other_machine_id] = other_was_primary
                        cls.sync_connections[other_machine_id] = connection
                    break
                except:
                    pass

        threads = []
        for i in range(len(cls.machines_down)):
            if i == machine_id:
                continue
            threads.append(Thread(target=connect_to_queue, args=[i]))
            threads.append(Thread(target=connect_to_sync, args=[i]))
        for i in range(len(cls.machines_down)):
            if i == machine_id:
                continue
            threads.append(Thread(target=accept_on_queue, args=[]))
            threads.append(Thread(target=accept_on_sync, args=[]))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        def handle_queue_connection(other_machine_id, connection):
            try:
                while True:
                    req = connection.recv(1024)
                    if len(req) == 0:
                        break
                    with cls.machine_lock:
                        if not cls.is_primary():
                            for i in range(len(cls.machines_down)):
                                if i == cls.machine_id:
                                    break
                                cls.machines_down[i] = True
                                cls.persist_primary_log()
                    opcode = DatabaseOpcode(BaseRequest.peek_opcode(req))
                    request = None
                    response = None
                    match opcode:
                        case DatabaseOpcode.DELETE_ACCOUNT:
                            request = (DatabaseRequests.DeleteAccount
                                    .deserialize(req))
                            cls.delete_account(account=request.get_account())
                            response = DatabaseResponses.DeleteAccount()
                        case DatabaseOpcode.DELETE_ALL:
                            request = (DatabaseRequests.DeleteAll
                                    .deserialize(req))
                            cls.delete_all()
                            response = DatabaseResponses.DeleteAll()
                        case DatabaseOpcode.GET_ACCOUNT_LOGGED_IN:
                            request = (DatabaseRequests.GetAccountLoggedIn
                                        .deserialize(req))
                            response = DatabaseResponses.GetAccountLoggedIn(
                                logged_in=cls.get_account_logged_in(
                                    account=request.get_account()
                                )
                            )
                        case DatabaseOpcode.GET_ACCOUNTS:
                            request = (DatabaseRequests.GetAccounts
                                    .deserialize(req))
                            response = DatabaseResponses.GetAccounts(
                                accounts=[v for v in cls.get_accounts().values()]
                            )
                        case DatabaseOpcode.GET_MESSAGES:
                            request = (DatabaseRequests.GetMessages
                                    .deserialize(req))
                            response = DatabaseResponses.GetMessages(
                                messages=cls.get_messages(
                                    account=request.get_account(),
                                    logged_in=request.get_logged_in()
                                )
                            )
                        case DatabaseOpcode.HAS_ACCOUNT:
                            request = (DatabaseRequests.HasAccount
                                    .deserialize(req))
                            response = DatabaseResponses.HasAccount(
                                has_account=cls.has_account(
                                    account=request.get_account()
                                )
                            )
                        case DatabaseOpcode.UPSERT_ACCOUNT:
                            request = (DatabaseRequests.UpsertAccount
                                    .deserialize(req))
                            cls.upsert_account(account=request.get_account())
                            response = DatabaseResponses.UpsertAccount()
                        case DatabaseOpcode.UPSERT_MESSAGE:
                            request = (DatabaseRequests.UpsertMessage
                                        .deserialize(req))
                            cls.upsert_message(message=request.get_the_message())
                            response = DatabaseResponses.UpsertMessage()
                    connection.sendall(response.serialize())
            except:
                pass
            finally:
                with cls.machine_lock:
                    cls.machines_down[other_machine_id] = True
                    cls.persist_primary_log()

        def handle_sync_connection(other_machine_id, connection):
            try:
                while True:
                    req = connection.recv(1024)
                    if len(req) == 0:
                        break
                    request = DatabaseRequests.SyncData.deserialize(req)
                    with cls.machine_lock:
                        cls._accounts = {}
                        cls._messages = {}

                        for account in request.get_accounts():
                            cls.local_upsert_account(account)
                        for message in request.get_messages():
                            cls.local_upsert_message(message)

                        cls.persist_accounts()
                        cls.persist_messages()
                    connection.sendall(b'')
            except:
                pass
            finally:
                with cls.machine_lock:
                    cls.machines_down[other_machine_id] = True
                    cls.persist_primary_log()

        listener_threads = ([Thread(target=handle_queue_connection,
                                    args=[id, conn])
                             for id, conn in cls.queue_connections.items()] +
                            [Thread(target=handle_sync_connection,
                                    args=[id, conn])
                             for id, conn in cls.sync_connections.items()])

        for thread in listener_threads:
            thread.start()

        with cls.machine_lock:
            old_primary = None
            for i in range(len(cls.machines_down)):
                if was_primarys[i]:
                    old_primary = i
            if old_primary is not None and old_primary == cls.machine_id:
                for i in range(len(cls.machines_down)):
                    if i != cls.machine_id:
                        cls.sync(i)
            cls.persist_primary_log()

    @classmethod
    def accounts_file_name(cls):
        return "accounts" + str(cls.machine_id) + ".txt"

    @classmethod
    def messages_file_name(cls):
        return "messages" + str(cls.machine_id) + ".txt"

    @classmethod
    def primary_log_file_name(cls):
        return "primary" + str(cls.machine_id) + ".txt"

    @classmethod
    def deserialize_accounts(cls, data: bytes):
        return SerializationUtils.deserialize_list(
            data,
            Account.deserialize,
            lambda v: v.serialize()
        )

    # MUST HOLD machine_lock
    @classmethod
    def serialize_accounts(cls):
        return SerializationUtils.serialize_list(
            [v for v in cls._accounts.values()],
            lambda v: v.serialize()
        )

    # MUST HOLD machine_lock
    @classmethod
    def persist_accounts(cls):
        if len(cls._accounts) == 0:
            return
        with open(cls.accounts_file_name(), "wb+") as file:
            file.write(cls.serialize_accounts())

    @classmethod
    def deserialize_messages(cls, data: bytes):
        return SerializationUtils.deserialize_list(
            data,
            Message.deserialize,
            lambda v: v.serialize()
        )

    # MUST HOLD machine_lock
    @classmethod
    def serialize_messages(cls):
        return SerializationUtils.serialize_list(
            [vv for v in cls._messages.values() for vv in v],
            lambda v: v.serialize()
        )

    # MUST HOLD machine_lock
    @classmethod
    def persist_messages(cls):
        if len(cls._messages) == 0:
            return
        with open(cls.messages_file_name(), "wb+") as file:
            file.write(cls.serialize_messages())

    # MUST HOLD machine_lock
    @classmethod
    def persist_primary_log(cls):
        with open(cls.primary_log_file_name(), "w+") as file:
            file.write("1" if cls.is_primary() else "0")

    # MUST HOLD machine_lock
    @classmethod
    def get_primary_id(cls):
        for i in range(len(cls.machines_down)):
            if not cls.machines_down[i]:
                return i
        return None

    # MUST HOLD machine_lock
    @classmethod
    def is_primary(cls):
        return cls.get_primary_id() == cls.machine_id

    # MUST HOLD machine_lock
    @classmethod
    def get_replicas(cls):
        skipped_primary = False
        replicas = []
        for i in range(len(cls.machines_down)):
            if not cls.machines_down[i]:
                if not skipped_primary:
                    skipped_primary = True
                else:
                    replicas.append(i)
        return replicas

    # MUST HOLD machine_lock
    @classmethod
    def sync(cls, other_machine_id):
        if len(cls._accounts) == 0 and len(cls._messages) == 0:
            return
        request = DatabaseRequests.SyncData(
            accounts=[v for v in cls._accounts.values()],
            messages=[vv for v in cls._messages.values() for vv in v]
        )
        cls.sync_sockets[other_machine_id].sendall(request.serialize())

    # MUST HOLD machine_lock
    @classmethod
    def sync_with_replicas(cls):
        replicas = cls.get_replicas()
        for other_machine_id in replicas:
            try:
                cls.sync(other_machine_id)
            except:
                cls.machines_down[other_machine_id] = True
                cls.persist_primary_log()

    # MUST HOLD machine_lock
    @classmethod
    def proxy(cls,
              opcode,
              account=None,
              logged_in=None,
              message=None):
        primary_id = cls.get_primary_id()
        request = None
        match opcode:
            case DatabaseOpcode.DELETE_ACCOUNT:
                request = DatabaseRequests.DeleteAccount(
                    account=account
                )
            case DatabaseOpcode.DELETE_ALL:
                request = DatabaseRequests.DeleteAll()
            case DatabaseOpcode.GET_ACCOUNT_LOGGED_IN:
                request = DatabaseRequests.GetAccountLoggedIn(
                    account=account
                )
            case DatabaseOpcode.GET_ACCOUNTS:
                request = DatabaseRequests.GetAccounts()
            case DatabaseOpcode.GET_MESSAGES:
                request = DatabaseRequests.GetMessages(
                    account=account,
                    logged_in=logged_in
                )
            case DatabaseOpcode.HAS_ACCOUNT:
                request = DatabaseRequests.HasAccount(
                    account=account
                )
            case DatabaseOpcode.UPSERT_ACCOUNT:
                request = DatabaseRequests.UpsertAccount(
                    account=account
                )
            case DatabaseOpcode.UPSERT_MESSAGE:
                request = DatabaseRequests.UpsertMessage(
                    the_message=message
                )
        try:
            cls.queue_sockets[primary_id].sendall(request.serialize())
            response = b''
            while len(response) == 0:
                response = cls.queue_sockets[primary_id].recv(1024)
        except:
            cls.machines_down[cls.get_primary_id()] = True
            cls.persist_primary_log()
            match opcode:
                case DatabaseOpcode.DELETE_ACCOUNT:
                    cls.delete_account(account=account)
                    return
                case DatabaseOpcode.DELETE_ALL:
                    cls.delete_all()
                    return
                case DatabaseOpcode.GET_ACCOUNT_LOGGED_IN:
                    return cls.get_account_logged_in(account=account)
                case DatabaseOpcode.GET_ACCOUNTS:
                    return cls.get_accounts()
                case DatabaseOpcode.GET_MESSAGES:
                    return cls.get_messages(account=account,
                                            logged_in=logged_in)
                case DatabaseOpcode.HAS_ACCOUNT:
                    return cls.has_account(account=account)
                case DatabaseOpcode.UPSERT_ACCOUNT:
                    cls.upsert_account(account=account)
                    return
                case DatabaseOpcode.UPSERT_MESSAGE:
                    cls.upsert_message(message=message)
                    return
        opcode = DatabaseOpcode(BaseRequest.peek_opcode(response))
        match opcode:
            case DatabaseOpcode.GET_ACCOUNT_LOGGED_IN:
                return (DatabaseResponses.GetAccountLoggedIn
                        .deserialize(response)
                        .get_logged_in())
            case DatabaseOpcode.GET_ACCOUNTS:
                return {account.get_username(): account
                        for account in (DatabaseResponses.GetAccounts
                                        .deserialize(response)
                                        .get_accounts())}
            case DatabaseOpcode.GET_MESSAGES:
                return (DatabaseResponses.GetMessages
                        .deserialize(response)
                        .get_messages())
            case DatabaseOpcode.HAS_ACCOUNT:
                return (DatabaseResponses.HasAccount
                        .deserialize(response)
                        .get_has_account())
            case _:
                # success; method is a `void`
                return

    @classmethod
    def upsert_account(cls, account: Account):
        """Update or insert an `Account`.
        """
        with cls.machine_lock:
            if cls.is_primary():
                cls.local_upsert_account(account)
                cls.persist_accounts()
                cls.sync_with_replicas()
            else:
                return cls.proxy(DatabaseOpcode.UPSERT_ACCOUNT, 
                                 account=account)

    # MUST HOLD machine_lock
    @classmethod
    def local_upsert_account(cls, account: Account):
        cls._accounts[account.get_username()] = account

    @classmethod
    def get_accounts(cls):
        """Get the entire `_accounts` table...
        """
        with cls.machine_lock:
            if cls.is_primary():
                return {k: v for k, v in cls._accounts.items()}
            else:
                return cls.proxy(DatabaseOpcode.GET_ACCOUNTS)

    @classmethod
    def get_account_logged_in(cls, account: Account):
        """Get whether a particular `account` is logged in according to the db.
        """
        with cls.machine_lock:
            if cls.is_primary():
                username = account.get_username()
                if username in cls._accounts:
                    return cls._accounts[username].get_logged_in()
            else:
                return cls.proxy(DatabaseOpcode.GET_ACCOUNT_LOGGED_IN, 
                                 account=account)

    @classmethod
    def has_account(cls, account: Account):
        """See whether a particular `account` is in the db.
        """
        with cls.machine_lock:
            if cls.is_primary():
                return account.get_username() in cls._accounts
            else:
                return cls.proxy(DatabaseOpcode.HAS_ACCOUNT, 
                                 account=account)

    @classmethod
    def upsert_message(cls, message: Message):
        """Update or insert a `Message`.
        """
        with cls.machine_lock:
            if cls.is_primary():
                cls.local_upsert_message(message)
                cls.persist_messages()
                cls.sync_with_replicas()
            else:
                return cls.proxy(DatabaseOpcode.UPSERT_MESSAGE, 
                                 message=message)

    # MUST HOLD machine_lock
    @classmethod
    def local_upsert_message(cls, message: Message):
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
        """Get the `Message`s sent to the `Account`.
        """
        with cls.machine_lock:
            if cls.is_primary():
                recipient_username = account.get_username()
                if recipient_username not in cls._messages:
                    return []
                messages = cls._messages[recipient_username]
                return [msg for msg in messages
                        if not msg.get_delivered() and
                        (not logged_in or msg.get_recipient_logged_in())]
            else:
                return cls.proxy(DatabaseOpcode.GET_MESSAGES,
                                 account=account, 
                                 logged_in=logged_in)

    @classmethod
    def delete_account(cls, account: Account):
        """Delete an `Account`, and all `Message`s to it.
        """
        with cls.machine_lock:
            if cls.is_primary():
                username = account.get_username()
                cls._accounts.pop(username, None)
                cls._messages.pop(username, None)
                cls.persist_accounts()
                cls.persist_messages()
                cls.sync_with_replicas()
                return
            else:
                return cls.proxy(DatabaseOpcode.DELETE_ACCOUNT, 
                                 account=account)

    @classmethod
    def delete_all(cls):
        with cls.machine_lock:
            if cls.is_primary():
                cls._accounts = {}
                cls._messages = {}
                cls.persist_accounts()
                cls.persist_messages()
                cls.sync_with_replicas()
                return
            else:
                return cls.proxy(DatabaseOpcode.DELETE_ALL)
