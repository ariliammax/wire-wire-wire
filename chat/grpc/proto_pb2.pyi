from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Account(_message.Message):
    __slots__ = ["logged_in", "username"]
    LOGGED_IN_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    logged_in: bool
    username: str
    def __init__(self, logged_in: bool = ..., username: _Optional[str] = ...) -> None: ...

class CreateAccountRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class CreateAccountResponse(_message.Message):
    __slots__ = ["error"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...

class DeleteAccountRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class DeleteAccountResponse(_message.Message):
    __slots__ = ["error"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...

class DeliverUndeliveredMessagesRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class DeliverUndeliveredMessagesResponse(_message.Message):
    __slots__ = ["error", "messages"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    error: str
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    def __init__(self, error: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...

class ListAccountsRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListAccountsResponse(_message.Message):
    __slots__ = ["accounts", "error"]
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    accounts: _containers.RepeatedCompositeFieldContainer[Account]
    error: str
    def __init__(self, error: _Optional[str] = ..., accounts: _Optional[_Iterable[_Union[Account, _Mapping]]] = ...) -> None: ...

class LogInAccountRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class LogInAccountResponse(_message.Message):
    __slots__ = ["error"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["delivered", "message", "recipient_username", "sender_username", "time"]
    DELIVERED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_USERNAME_FIELD_NUMBER: _ClassVar[int]
    SENDER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    delivered: bool
    message: str
    recipient_username: str
    sender_username: str
    time: int
    def __init__(self, delivered: bool = ..., message: _Optional[str] = ..., recipient_username: _Optional[str] = ..., sender_username: _Optional[str] = ..., time: _Optional[int] = ...) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ["message", "recipient_username", "sender_username"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_USERNAME_FIELD_NUMBER: _ClassVar[int]
    SENDER_USERNAME_FIELD_NUMBER: _ClassVar[int]
    message: str
    recipient_username: str
    sender_username: str
    def __init__(self, message: _Optional[str] = ..., recipient_username: _Optional[str] = ..., sender_username: _Optional[str] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ["error"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...
