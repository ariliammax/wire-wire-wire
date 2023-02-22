# tests.py

from chat.common.config import Config
from chat.common.models import Account
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
from threading import Thread
from time import sleep

import pytest


# HELPERS


class Chat(Enum):
    GRPC = 0
    WIRE = 1


class TestData():
    message = "hi"
    username = "username"
    username2 = "username2"


def start_client(chat: Chat, host="localhost", port=Config.PORT):
    match chat:
        case Chat.GRPC:
            return grpc_client_entry(host=host, port=port)
        case Chat.WIRE:
            return wire_client_entry(host=host, port=port + 1)


def start_server(chat: Chat, host="localhost", port=Config.PORT):
    match chat:
        case Chat.GRPC:
            grpc_server_main(port=port)
        case Chat.WIRE:
            wire_server_main(host=host, port=port + 1)


def start_server_thread(chat: Chat):
    thread = Thread(target=start_server, args=[chat])
    thread.daemon = True
    thread.start()


def request(chat: Chat, opcode: Opcode, **kwargs):
    match chat:
        case Chat.GRPC:
            return grpc_client_request(opcode, **kwargs)
        case Chat.WIRE:
            return wire_client_request(opcode, **kwargs)


def clean_between_tests():
    Database.delete_all()


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


def deliver_undelivered_messages(chat: Chat, username: str, **kwargs):
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
                   username=TestData.username,
                   **kwargs)


# TESTS


@pytest.fixture(scope="session")
def kwargs():
    kwargs = {}
    for chat in [Chat.WIRE, Chat.GRPC]:
        start_server_thread(chat)
        sleep(0.1)
        kwargs.update(start_client(chat))
    return kwargs


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_create_account_success(chat: Chat, kwargs):
    clean_between_tests()

    response = create_account(chat, **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_create_account_error(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = create_account(chat, **kwargs)
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_log_in_account_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = log_in_account(chat, **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_log_in_account_error(chat: Chat, kwargs):
    clean_between_tests()

    response = log_in_account(chat, **kwargs)
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_list_accounts_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)
    account = Account(logged_in=True, username=TestData.username)

    response = list_accounts(chat, "", **kwargs)
    assert (response.get_accounts() == [account])

    response = list_accounts(chat, TestData.username, **kwargs)
    assert (response.get_accounts() == [account])

    clean_between_tests()
    create_account(chat, **kwargs)
    create_account(chat, username=TestData.username2, **kwargs)
    account2 = Account(logged_in=True, username=TestData.username2)

    response = list_accounts(chat, "", **kwargs)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username, **kwargs)
    assert (response.get_accounts() == [account, account2])

    response = list_accounts(chat, TestData.username2, **kwargs)
    assert (response.get_accounts() == [account2])


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_list_accounts_error(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = list_accounts(chat, TestData.username2, **kwargs)
    assert (len(response.get_accounts()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_send_message_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)
    create_account(chat, username=TestData.username2, **kwargs)

    response = send_message(chat,
                            recipient_username=TestData.username,
                            message=TestData.message,
                            **kwargs)
    assert (len(response.get_error()) == 0)

    response = send_message(chat,
                            recipient_username=TestData.username2,
                            message=TestData.message,
                            **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_send_message_error(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = send_message(chat,
                            recipient_username=TestData.username2,
                            message=TestData.message,
                            **kwargs)
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_deliver_undelivered_messages_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    send_message(chat,
                 recipient_username=TestData.username,
                 message=TestData.message,
                 **kwargs)

    response = deliver_undelivered_messages(chat,
                                            username=TestData.username,
                                            **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_deliver_undelivered_messages_error(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = deliver_undelivered_messages(chat,
                                            username=TestData.username,
                                            **kwargs)
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_delete_account_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = delete_account(chat, **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_delete_account_error(chat: Chat, kwargs):
    clean_between_tests()

    response = delete_account(chat, **kwargs)
    assert (len(response.get_error()) != 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_log_out_account_success(chat: Chat, kwargs):
    clean_between_tests()
    create_account(chat, **kwargs)

    response = log_out_account(chat, **kwargs)
    assert (len(response.get_error()) == 0)


@pytest.mark.parametrize("chat", [Chat.WIRE, Chat.GRPC])
def test_log_out_account_error(chat: Chat, kwargs):
    clean_between_tests()

    response = log_out_account(chat, **kwargs)
    assert (len(response.get_error()) != 0)
