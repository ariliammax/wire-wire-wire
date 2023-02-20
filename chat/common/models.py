# models.py
# in chat.common

from chat.common.operations import Opcode
from chat.common.serialization import SerializationUtils
from chat.common.util import Model
from typing import Callable, Dict, List

# DATA MODELS


Account = Model.model_with_fields(logged_in=bool,
                                  username=str)


Message = Model.model_with_fields(delivered=bool,
                                  message=str,
                                  recipient_username=str,
                                  sender_username=str,
                                  time=int)


# OBJECT MODELS

# these are the basic ones.
class BaseRequest(Model.model_with_fields(opcode=int)):
    @staticmethod
    def deserialize_opcode(data: bytes) -> int:
        return SerializationUtils.deserialize_int(data[:1])

    @staticmethod
    def serialize_opcode(val: int) -> bytes:
        return SerializationUtils.serialize_int(val, length=1)

    @staticmethod
    def peek_opcode(data: bytes) -> Opcode:
        return Opcode(BaseRequest.deserialize_opcode(data[:1]))

    @staticmethod
    def add_fields_with_opcode(opcode: int,
                               field_defaults: Dict[str, object] = {},
                               field_deserializers: Dict[str, Callable] = {},
                               field_serializers: Dict[str, Callable] = {},
                               order_of_fields: List[str] = None,
                               **new_fields: Dict[str, type]):
        class __impl_class__(
            BaseRequest.add_fields(
                field_defaults=dict(list(field_defaults.items()) +
                                    list(dict(opcode=opcode.value).items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('opcode',
                                           BaseRequest.deserialize_opcode)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('opcode',
                                         BaseRequest.serialize_opcode)]),
                order_of_fields=(order_of_fields or
                                 (['opcode'] +
                                  list(new_fields.keys()))),
                **new_fields)):
            pass

        return __impl_class__


class BaseResponse(BaseRequest, BaseRequest.add_fields(error=str)):
    pass


# Function 0: Log In Account
LogInAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.LOGIN_ACCOUNT)
LogInAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.LOGIN_ACCOUNT)

# Function 1: Create Account
CreateAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.CREATE_ACCOUNT)
CreateAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.CREATE_ACCOUNT)


# Function 2: List Accounts
# TODO: search string
ListAccountsRequest = BaseRequest.add_fields_with_opcode(
    opcode=Opcode.LIST_ACCOUNTS)
ListAccountsResponse = BaseResponse.add_fields_with_opcode(
    accounts=list,
    opcode=Opcode.LIST_ACCOUNTS,
    field_deserializers=dict(
        accounts=Model.default_list_deserializer(Account)),
    field_serializers=dict(
        accounts=Model.default_list_serializer(Account)))


# Function 3: Send Message
SendMessageRequest = BaseRequest.add_fields_with_opcode(
    message=str,
    recipient_username=str,
    sender_username=str,
    opcode=Opcode.SEND_MESSAGE)
SendMessageResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.SEND_MESSAGE)


# Function 4: Deliver Undelivered Messages
DeliverUndeliveredMessagesRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.DELIVER_UNDELIVERED_MESSAGES)
DeliverUndeliveredMessagesResponse = BaseResponse.add_fields_with_opcode(
    messages=list,
    opcode=Opcode.DELIVER_UNDELIVERED_MESSAGES,
    field_deserializers=dict(
        messages=Model.default_list_deserializer(Message)),
    field_serializers=dict(
        messages=Model.default_list_serializer(Message)))


# Function 5: Delete Account
DeleteAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.DELETE_ACCOUNT)
DeleteAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.DELETE_ACCOUNT)
