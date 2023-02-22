# tests.py

from chat.common.config import Config
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


class Chat(Enum):
    GRPC = 0
    WIRE = 1


def start_client(chat: Chat, host='localhost', port=Config.PORT):
    match chat:
        case Chat.GRPC:
            return grpc_client_entry(host=host, port=port)
        case Chat.WIRE:
            return wire_client_entry(host=host, port=port + 1)


def start_server(chat: Chat, host='localhost', port=Config.PORT):
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


class Tests:

    @staticmethod
    def clean_between_tests():
        Database.delete_all()

    @staticmethod
    def run_create_account_success(chat: Chat, **kwargs):
        # Test 1 - create account works
        response = request(chat,
                           Opcode.CREATE_ACCOUNT,
                           username="username",
                           **kwargs)
        assert (response.get_error() == '')

    @staticmethod
    def run_create_account_fail(chat: Chat, **kwargs):
        # Test 2 - create already created account fails
        Tests.run_create_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.CREATE_ACCOUNT,
                           username="username",
                           **kwargs)
        assert (response.get_error() != '')

    @staticmethod
    def run_log_in_account_success(chat: Chat, **kwargs):
        # Test 3 - log in account works
        Tests.run_create_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.LOG_IN_ACCOUNT,
                           username="username",
                           **kwargs)
        assert (response.get_error() == '')

    @staticmethod
    def run_log_in_account_fail(chat: Chat, **kwargs):
        # Test 4 - log in nonexistant account fails
        response = request(chat,
                           Opcode.LOG_IN_ACCOUNT,
                           username="username",
                           **kwargs)
        assert (response.get_error() != '')

    @staticmethod
    def run_list_accounts_success(chat: Chat, **kwargs):
        # Test 3 - list accounts works
        Tests.run_log_in_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.LIST_ACCOUNTS,
                           text_wildcard="username",
                           **kwargs)
        assert (len(response.get_accounts()) == 1)

    @staticmethod
    def run_list_accounts_fail(chat: Chat, **kwargs):
        # Test 4 - list account "fails"
        Tests.run_log_in_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.LIST_ACCOUNTS,
                           text_wildcard="username2",
                           **kwargs)
        assert (len(response.get_accounts()) == 0)

    @staticmethod
    def run_send_message_success(chat: Chat, **kwargs):
        # Test 3 - list accounts works
        Tests.run_log_in_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.SEND_MESSAGE,
                           sender_username="username",
                           recipient_username="username",
                           message="hi",
                           **kwargs)
        assert (response.get_error() == '')

    @staticmethod
    def run_send_message_fail(chat: Chat, **kwargs):
        # Test 4 - list account "fails"
        Tests.run_log_in_account_success(chat, **kwargs)
        response = request(chat,
                           Opcode.SEND_MESSAGE,
                           sender_username="username",
                           recipient_username="bad",
                           message="hi",
                           **kwargs)
        assert (response.get_error() != '')


def run_tests(chat: Chat):
    start_server_thread(chat)
    sleep(0.1)
    kwargs = start_client(chat)

    # Create accounts test
    Tests.run_create_account_success(chat, **kwargs)
    Tests.clean_between_tests()
    Tests.run_create_account_fail(chat, **kwargs)
    Tests.clean_between_tests()

    # Login accounts test
    Tests.run_log_in_account_success(chat, **kwargs)
    Tests.clean_between_tests()
    Tests.run_log_in_account_fail(chat, **kwargs)
    Tests.clean_between_tests()

    # List accounts test
    Tests.run_list_accounts_success(chat, **kwargs)
    Tests.clean_between_tests()
    Tests.run_list_accounts_fail(chat, **kwargs)
    Tests.clean_between_tests()

    # Send messages test
    Tests.run_send_message_success(chat, **kwargs)
    Tests.clean_between_tests()
    Tests.run_send_message_fail(chat, **kwargs)
    Tests.clean_between_tests()

    return


def test_wire():
    run_tests(Chat.WIRE)


def test_grpc():
    run_tests(Chat.GRPC)
