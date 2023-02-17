# events.py
# in chat.common.client

import typing  # noqa

from chat.common.operations import Opcode
from typing import Callable


def main(entry: Callable, request: Callable, handler: Callable, **kwargs):
    """A nice (TM) generic way of handling the event logic shared by the wire
       and gRPC protocols.
       `entry` is called once at the beginning, to establish the connection
        (or whatever other setup you want to do). Note that `kwargs` will be
        set to the return value of `entry` here, so it can pass the connections
        onwards to `request` and `handler`.
       `request` does requests across the connection,
       `handler` handles errors.
    """
    try:
        kwargs = entry(**kwargs)

        username = input("> Username: ")

        response = request(Opcode.CREATE_ACCOUNT, username, **kwargs)
        print(response)

        while True:
            print(
                (
                    "Do you want to...\n"
                    "1) List Accounts\n"
                    "2) Send a Message\n"
                    "3) Deliver Undelivered Messages\n"
                    "4) Delete Account\n"
                )
            )
            opcode = input("> 1/2/3/4: ")
            opcode = int(opcode) + 1
            if (opcode == Opcode.LIST_ACCOUNTS.value):
                response = request(Opcode.LIST_ACCOUNTS, **kwargs)
                print("\nAccounts:\n[" + response + "]\n")
            elif (opcode == Opcode.SEND_MESSAGE.value):
                recipient = input("> Recipient: ")
                message = input("> Message: ")
                response = request(
                    Opcode.SEND_MESSAGE, 
                    message, 
                    recipient, 
                    username, 
                    **kwargs)
                print("Message was sent!")
            elif (opcode == Opcode.DELIVER_UNDELIVERED_MESSAGES.value):
                response = request(Opcode.DELIVER_UNDELIVERED_MESSAGES, username, **kwargs)
                print(response)
            elif (opcode == Opcode.DELETE_ACCOUNT.value):
                response = request(Opcode.DELETE_ACCOUNT, **kwargs)
                break
    except Exception as err:
        handler(err=err, **kwargs)
