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


def start_client(chat: Chat):
    match chat:
        case Chat.GRPC:
            return grpc_client_entry(Config.HOST, Config.PORT)
        case Chat.WIRE:
            return wire_client_entry(Config.HOST, Config.PORT + 1)


def start_server(chat: Chat):
    match chat:
        case Chat.GRPC:
            grpc_server_main(Config.PORT)
        case Chat.WIRE:
            wire_server_main(Config.HOST, Config.PORT + 1)


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


def run_tests(chat: Chat):
    start_server_thread(chat)
    sleep(0.1)
    kwargs = start_client(chat)

    # Test 1
    response = request(chat,
                       Opcode.CREATE_ACCOUNT,
                       username="username",
                       **kwargs)
    assert (response.get_error() == '')
    Database.delete_all()

    # Test 2
    response = request(chat,
                       Opcode.CREATE_ACCOUNT,
                       username="username",
                       **kwargs)
    assert (response.get_error() == '')
    response = request(chat,
                       Opcode.CREATE_ACCOUNT,
                       username="username",
                       **kwargs)
    assert (response.get_error() != '')
    Database.delete_all()


def test_wire():
    run_tests(Chat.WIRE)


def test_grpc():
    run_tests(Chat.GRPC)
