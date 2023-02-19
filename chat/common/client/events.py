# events.py
# in chat.common.client

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

        username = input('> Username: ')

        response = request(opcode=Opcode.CREATE_ACCOUNT,
                           username=username,
                           **kwargs)
        print(response)

        while True:
            print('Do you want to...\n'
                  '1) List Accounts\n'
                  '2) Send a Message\n'
                  '3) Deliver Undelivered Messages\n'
                  '4) Delete Account\n')
            opcode = input('> 1/2/3/4: ')

            # + 1 since Opcode.CREATE_ACCOUNT has value 0.
            opcode = Opcode(int(opcode) + 1)
            match opcode:
                case Opcode.LIST_ACCOUNTS:
                    response = request(opcode=Opcode.LIST_ACCOUNTS,
                                       **kwargs)
                    print('\nAccounts:\n[' + response + ']\n')
                case Opcode.SEND_MESSAGE:
                    recipient = input('> Recipient: ')
                    message = input('> Message: ')
                    response = request(
                        opcode=Opcode.SEND_MESSAGE,
                        message=message,
                        recipient_username=recipient,
                        sender_username=username,
                        **kwargs)
                    print('\nYour message was sent!\n')
                case Opcode.DELIVER_UNDELIVERED_MESSAGES:
                    response = request(opcode=Opcode
                                       .DELIVER_UNDELIVERED_MESSAGES,
                                       username=username,
                                       **kwargs)
                    print('\n' + response + '\n')
                case Opcode.DELETE_ACCOUNT:
                    response = request(opcode=Opcode.DELETE_ACCOUNT,
                                       username=username,
                                       **kwargs)
                    break

    except Exception as err:
        handler(err=err, **kwargs)
