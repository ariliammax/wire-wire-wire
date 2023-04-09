# database.py
# in chat.common.server

from chat.common.config import Config
from chat.common.models import Account, BaseRequest, Message
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
        message=Message,
        opcode=DatabaseOpcode.UPSERT_MESSAGE.value
    )


class DatabaseResponses:
    DeleteAccount = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.DELETE_ACCOUNT.value
    )
    DeleteAll = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.DELETE_ALL.value
    )
    GetAccountLoggedIn = BaseRequest.add_fields_with_opcode(
        logged_in=bool,
        opcode=DatabaseOpcode.GET_ACCOUNT_LOGGED_IN.value
    )
    GetAccounts = BaseRequest.add_fields_with_opcode(
        accounts=list,
        fields_list_nested=dict(accounts=Account),
        opcode=DatabaseOpcode.GET_ACCOUNTS.value
    )
    GetMessages = BaseRequest.add_fields_with_opcode(
        messages=list,
        fields_list_nested=dict(messages=Message),
        opcode=DatabaseOpcode.GET_MESSAGES.value
    )
    HasAccount = BaseRequest.add_fields_with_opcode(
        has_account=bool,
        opcode=DatabaseOpcode.HAS_ACCOUNT.value
    )
    UpsertAccount = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.UPSERT_ACCOUNT.value
    )
    UpsertMessage = BaseRequest.add_fields_with_opcode(
        opcode=DatabaseOpcode.UPSERT_MESSAGE.value
    )


class Database(object):
    """A `Database` for the chat programs.
    """

    # key is username
    _accounts: Dict[str, Account] = {}

    # key is recipient_username
    _messages: Dict[str, Message] = {}

    machines_down: list = [False, False, False]
    machine_id: int = None
    machine_lock: Lock = Lock()

    queue_sockets: dict = {}
    sync_sockets: dict = {}
    queue_connections: dict = {}
    sync_connections: dict = {}

    @classmethod
    def startup(cls, machine_id=0):
        with cls.machine_lock:
            cls.machine_id = machine_id

            try:
                with open(cls.accounts_file_name(), "r") as file:
                    lines = file.readlines()
                    for line in lines:
                        values = line[:-1].split(",") # removes \n
                        account = (
                            Account()
                            .set_logged_in(values[0] == "1")
                            .set_username(values[1])
                        )
                        cls._accounts[account.get_username()] = account
            except FileNotFoundError:
                pass

            try:
                with open(cls.messages_file_name(), "r") as file:
                    lines = file.readlines()
                    for line in lines:
                        values = line[:-1].split(",") # removes \n
                        message = (
                            Message()
                            .set_delivered(values[0] == "1")
                            .set_message(values[1])
                            .set_recipient_logged_in(values[2] == "1")
                            .set_recipient_username(values[3])
                            .set_sender_username(values[4])
                            .set_time(int(values[5]))
                        )
                        username = message.get_recipient_username()
                        if username not in cls._messages:
                            cls._messages[username] = []
                        cls._messages[username].append(message)
            except FileNotFoundError:
                pass

            host, port = Config.ADDRESSES[machine_id]

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
            other_host, other_port = Config.ADDRESSES[other_machine_id]
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
            other_host, other_port = Config.ADDRESSES[other_machine_id]
            other_port += 2
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(Config.TIMEOUT_SYNC)
                    s.connect((other_host, other_port))
                    s.sendall(int.to_bytes(machine_id, 1, byteorder='little'))
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
                    other_machine_id = int.from_bytes(request, byteorder='little')
                    with cls.machine_lock:
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
            while True:
                req = connection.recv(1024)
                with cls.machine_lock:
                    if not cls.is_master():
                        for i in range(len(cls.machines_down)):
                            if i == cls.machine_id:
                                break
                            cls.machines_down[i] = True
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
                            accounts=cls.get_accounts()
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
                        response = DatabaseResponses.UpsertAccount
                    case DatabaseOpcode.UPSERT_MESSAGE:
                        request = (DatabaseRequests.UpsertMessage
                                    .deserialize(req))
                        cls.upsert_message(message=request.get_message())
                        response = DatabaseResponses.UpsertMessage
                connection.sendall(response.serialize())

        def handle_sync_connection(other_machine_id, connection):
            while True:
                req = connection.recv(1024).decode('utf-8')
                with cls.machine_lock:
                    print('rec', req)
                    accounts_string, messages_string = req.split("|")
                    cls.persist_accounts(accounts_string) # TODO: in-memory
                    cls.persist_messages(messages_string) # TODO: in-memory

        listener_threads = ([Thread(target=handle_queue_connection,
                                    args=[id, conn])
                             for id, conn in cls.queue_connections.items()] +
                            [Thread(target=handle_sync_connection,
                                    args=[id, conn])
                             for id, conn in cls.sync_connections.items()])

        for thread in listener_threads:
            thread.start()

    @classmethod
    def accounts_file_name(cls):
        return "accounts" + str(cls.machine_id) + ".txt"

    @classmethod
    def messages_file_name(cls):
        return "messages" + str(cls.machine_id) + ".txt"

    # MUST HOLD machine_lock
    @classmethod
    def accounts_to_string(cls):
        results = []
        for account in cls._accounts.values():
            values = []
            values.append("1" if account.get_logged_in() else "0")
            values.append(account.get_username())
            results.append(",".join(values))
        return '\n'.join(results)

    # MUST HOLD machine_lock
    @classmethod
    def persist_accounts(cls, string=None):
        with open(cls.accounts_file_name(), "w+") as file:
            file.write(string if string is not None else cls.accounts_to_string())

    # MUST HOLD machine_lock
    @classmethod
    def messages_to_string(cls):
        results = []
        for messages in cls._messages.values():
            for message in messages:
                values = []
                values.append("1" if message.get_delivered() else "0")
                values.append(message.get_message())
                values.append("1" if message.get_recipient_logged_in() else "0")
                values.append(message.get_recipient_username())
                values.append(message.get_sender_username())
                values.append(str(message.get_time()))
                results.append(",".join(values))
        return '\n'.join(results)

    # MUST HOLD machine_lock
    @classmethod
    def persist_messages(cls, string=None):
        with open(cls.messages_file_name(), "w+") as file:
            file.write(string if string is not None else cls.messages_to_string())

    # MUST HOLD machine_lock
    @classmethod
    def get_master_id(cls):
        for i in range(len(cls.machines_down)):
            if not cls.machines_down[i]:
                return i
        return None

    # MUST HOLD machine_lock
    @classmethod
    def is_master(cls):
        return cls.get_master_id() == cls.machine_id

    # MUST HOLD machine_lock
    @classmethod
    def get_replicas(cls):
        skipped_master = False
        replicas = []
        for i in range(len(cls.machines_down)):
            if not cls.machines_down[i]:
                if not skipped_master:
                    skipped_master = True
                else:
                    replicas.append(i)
        return replicas

    # MUST HOLD machine_lock
    @classmethod
    def sync_with_replicas(cls):
        replicas = cls.get_replicas()
        for replica in replicas:
            try:
                s = cls.accounts_to_string()
                s += "|"
                s += cls.messages_to_string()
                print('send', s)
                cls.sync_sockets[replica].sendall(s.encode('utf-8'))
            except TimeoutError:
                cls.machines_down[replica] = True

    # MUST HOLD machine_lock
    @classmethod
    def proxy(cls,
              opcode,
              account=None,
              logged_in=None,
              message=None):
        master_id = cls.get_master_id()
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
                    message=message
                )
        try:
            cls.queue_sockets[master_id].sendall(request.serialize())
            response = cls.queue_connections[master_id].recv(1024)
        except TimeoutError:
            cls.machines_down[cls.get_master_id()] = True
            match opcode:
                case DatabaseOpcode.DELETE_ACCOUNT:
                    return cls.delete_account(account=account)
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
                return (DatabaseResponses.GetAccounts
                        .deserialize(response)
                        .get_accounts())
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
            if cls.is_master():
                cls._accounts[account.get_username()] = account
                cls.persist_accounts()
                cls.sync_with_replicas()
            else:
                return cls.proxy(DatabaseOpcode.UPSERT_ACCOUNT, 
                                 account=account)

    @classmethod
    def get_accounts(cls):
        """Get the entire `_accounts` table...
        """
        with cls.machine_lock:
            if cls.is_master():
                return {k: v for k, v in cls._accounts.items()}
            else:
                return cls.proxy(DatabaseOpcode.GET_ACCOUNTS)

    @classmethod
    def get_account_logged_in(cls, account: Account):
        """Get whether a particular `account` is logged in according to the db.
        """
        with cls.machine_lock:
            if cls.is_master():
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
            if cls.is_master():
                return account.get_username() in cls._accounts
            else:
                return cls.proxy(DatabaseOpcode.HAS_ACCOUNT, 
                                 account=account)

    @classmethod
    def upsert_message(cls, message: Message):
        """Update or insert a `Message`.
        """
        with cls.machine_lock:
            if cls.is_master():
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
                cls.persist_messages()
                cls.sync_with_replicas()
            else:
                return cls.proxy(DatabaseOpcode.UPSERT_MESSAGE, 
                                 message=message)

    @classmethod
    def get_messages(cls, account: Account, logged_in: bool):
        """Get the `Message`s sent to the `Account`.
        """
        with cls.machine_lock:
            if cls.is_master():
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
            if cls.is_master():
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
            if cls.is_master():
                cls._accounts = {}
                cls._messages = {}
                cls.persist_accounts()
                cls.persist_messages()
                cls.sync_with_replicas()
                return
            else:
                return cls.proxy(DatabaseOpcode.DELETE_ALL)
