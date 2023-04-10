# tests.py

from chat.common.config import Config
from chat.common.models import Message, Account
from chat.common.operations import Opcode
from chat.common.server.database import Database
from chat.grpc.client.main import (
    entry as grpc_client_entry,
    request as grpc_client_request,
)
from chat.grpc.server.main import main as grpc_server_main
from chat.wire.client.main import (
    entry as wire_client_entry,
    request as wire_client_request
)
from chat.wire.server.main import main as wire_server_main
from enum import Enum
from threading import Thread, Lock
from time import sleep

import chat.common.server.database
import pytest


# HELPERS


class Chat(Enum):
    GRPC = 0
    WIRE = 1


class TestData():
    # multiple of 100
    addresses = [('localhost', 10610),
                 ('localhost', 20610),
                 ('localhost', 30610)]
    message = "hi"
    username = "username"
    username2 = "username2"


class TestDatabases():
    def db_from_id(machine_id):
        class impl_db(Database):
            pass

        impl_db._accounts = {}
        impl_db._messages = {}
        impl_db.addresses = [v for v in TestData.addresses]
        impl_db.machines_down = [False, False, False]
        impl_db.machine_id = machine_id
        impl_db.machine_lock = Lock()
        impl_db.queue_sockets = {}
        impl_db.sync_sockets = {}
        impl_db.queue_connections = {}
        impl_db.sync_connections = {}

        return impl_db

    DBS = {Chat.GRPC: {0: db_from_id(0),
                       1: db_from_id(1),
                       2: db_from_id(2)},
           Chat.WIRE: {0: db_from_id(0),
                       1: db_from_id(1),
                       2: db_from_id(2)}}


def start_client(chat: Chat, machine_id=0):
    match chat:
        case Chat.GRPC:
            return grpc_client_entry(host=TestData.addresses[machine_id][0],
                                        port=TestData.addresses[machine_id][1])
        case Chat.WIRE:
            return wire_client_entry(host=TestData.addresses[machine_id][0],
                                        port=TestData.addresses[machine_id][1] + 10)


def start_server(chat_t: Chat,
                 machine_id=0):
    match chat_t:
        case Chat.GRPC:
            grpc_server_main(machine_id=machine_id,
                             addresses=TestData.addresses,
                             database=TestDatabases.DBS[chat_t][machine_id])
        case Chat.WIRE:
            wire_server_main(machine_id=machine_id,
                             addresses=[(host, port + 10)
                                        for host, port in TestData.addresses],
                             database=TestDatabases.DBS[chat_t][machine_id])


def start_server_thread(chat: Chat, machine_id=0):
    thread = Thread(target=start_server,
                     args=[chat],
                     kwargs=dict(machine_id=machine_id)
    )
    thread.start()


def request(chat: Chat, opcode: Opcode, **kwargs):
    match chat:
        case Chat.GRPC:
            return grpc_client_request(opcode, **kwargs)
        case Chat.WIRE:
            return wire_client_request(opcode, **kwargs)


def clean_between_tests(chat, machine_id):
    TestDatabases.DBS[chat][machine_id].delete_all()


def create_account(chat: Chat, username: str = None, **kwargs):
    username = username if username is not None else TestData.username
    return request(chat,
                   Opcode.CREATE_ACCOUNT,
                   username=username,
                   **kwargs)


def log_in_account(chat: Chat, username: str = None, **kwargs):
    username = username if username is not None else TestData.username
    return request(chat,
                   Opcode.LOG_IN_ACCOUNT,
                   username=username,
                   **kwargs)


def list_accounts(chat: Chat, text_wildcard: str, **kwargs):
    return request(chat,
                   Opcode.LIST_ACCOUNTS,
                   text_wildcard=text_wildcard,
                   **kwargs)


def send_message(chat: Chat, message: str, recipient_username: str, **kwargs):
    return request(chat,
                   Opcode.SEND_MESSAGE,
                   message=message,
                   recipient_username=recipient_username,
                   sender_username=TestData.username,
                   **kwargs)


def deliver_undelivered_messages(chat: Chat, username: str = None, **kwargs):
    username = username if username is not None else TestData.username
    return request(chat,
                   Opcode.DELIVER_UNDELIVERED_MESSAGES,
                   logged_in=False,
                   username=username,
                   **kwargs)


def delete_account(chat: Chat, username: str = None, **kwargs):
    username = username if username is not None else TestData.username
    return request(chat,
                   Opcode.DELETE_ACCOUNT,
                   username=username,
                   **kwargs)


def log_out_account(chat: Chat, username: str = None, **kwargs):
    username = username if username is not None else TestData.username
    return request(chat,
                   Opcode.LOG_OUT_ACCOUNT,
                   username=username,
                   **kwargs)


# TESTS


@pytest.fixture(scope="session")
def kwargs():
    kwargs = []
    for machine_id in range(3):
        for chat in [Chat.WIRE]:
            start_server_thread(chat, machine_id=machine_id)
    sleep(1)
    for machine_id in range(3):
        kwargs.append({})
        for chat in [Chat.WIRE]:
            kwargs[machine_id].update(start_client(chat,
                                                   machine_id=machine_id))
    return kwargs


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_create_account_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)

    response = create_account(chat, **kwargs[machine_id])
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_create_account_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = create_account(chat, **kwargs[0])
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_log_in_account_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = log_in_account(chat, **kwargs[0])
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_log_in_account_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)

    response = log_in_account(chat, **kwargs[0])
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_list_accounts_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])
    account = Account(logged_in=True, username=TestData.username)

    response = list_accounts(chat, "", **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])

    response = list_accounts(chat, TestData.username[1:-1], **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])

    response = list_accounts(chat, TestData.username, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])

    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])
    create_account(chat, username=TestData.username2, **kwargs[0])
    account2 = Account(logged_in=True, username=TestData.username2)

    response = list_accounts(chat, "", **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username[1:-1], **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username2, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account2])

    log_out_account(chat, username=TestData.username2, **kwargs[0])
    account2.set_logged_in(False)

    response = list_accounts(chat, "", **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username[1:-1], **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username2, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account2])

    delete_account(chat, username=TestData.username2, **kwargs[0])

    response = list_accounts(chat, "", **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])

    response = list_accounts(chat, TestData.username[1:-1], **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])

    response = list_accounts(chat, TestData.username, **kwargs[0])
    assert (len(response.get_error()) == 0)
    assert (response.get_accounts() == [account])


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_list_accounts_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = list_accounts(chat, TestData.username2, **kwargs[0])
    assert (len(response.get_accounts()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_send_message_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])
    create_account(chat, username=TestData.username2, **kwargs[0])

    response = send_message(chat,
                            recipient_username=TestData.username,
                            message=TestData.message,
                            **kwargs[0])
    assert (len(response.get_error()) == 0)

    response = send_message(chat,
                            recipient_username=TestData.username2,
                            message=TestData.message,
                            **kwargs[0])
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_send_message_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = send_message(chat,
                            recipient_username=TestData.username2,
                            message=TestData.message,
                            **kwargs[0])
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_deliver_undelivered_messages_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    message = (Message()
               .set_delivered(False)
               .set_message(TestData.message)
               .set_recipient_logged_in(True)
               .set_recipient_username(TestData.username)
               .set_sender_username(TestData.username)
               .set_time(None))

    send_message(chat,
                 recipient_username=TestData.username,
                 message=TestData.message,
                 **kwargs[0])

    response = deliver_undelivered_messages(chat,
                                            **kwargs[0])

    response_messages = response.get_messages()

    assert (len(response.get_error()) == 0)
    assert (len(response_messages) == 1)

    for response_message in response_messages:
        response_message.set_time(None)

    assert ([message] == response_messages)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_deliver_undelivered_messages_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = deliver_undelivered_messages(chat,
                                            username=TestData.username,
                                            **kwargs[0])
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_delete_account_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = delete_account(chat, **kwargs[0])
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_delete_account_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)

    response = delete_account(chat, **kwargs[0])
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_log_out_account_success(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)
    create_account(chat, **kwargs[0])

    response = log_out_account(chat, **kwargs[0])
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE])
@pytest.mark.parametrize("machine_id", range(3))
def test_log_out_account_error(chat: Chat, machine_id: int, kwargs):
    clean_between_tests(chat, machine_id)

    response = log_out_account(chat, **kwargs[0])
    assert (len(response.get_error()) != 0)
