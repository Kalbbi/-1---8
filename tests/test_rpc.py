"""Тесты RPC-протокола."""

import pytest
import socket
import threading
import time

from src.protocol import (
    decode_request,
    decode_response,
    encode_request,
    encode_response,
)

from src.server import (
    call_operation,
    element_to_value,
    make_response,
    parse_arguments,
    value_to_element,
)

from src.client import RPCClient
from src.server import handle_connection

PROTOCOL_VERSION = 1
TEST_REQUEST_OPERATION = 258
TEST_RESPONSE_OPERATION = 7
TEST_ERROR_OPERATION = 3
INVALID_REQUEST_OPERATION = 65536
INVALID_RESPONSE_OPERATION = 256
UNKNOWN_OPERATION = 999


def test_request_round_trip():
    message = encode_request(TEST_REQUEST_OPERATION, "<test>Привет</test>")
    operation, body = decode_request(message)

    assert message[0] == PROTOCOL_VERSION
    assert message[1:3] == b"\x01\x02"
    assert int.from_bytes(message[3:8], "big") == len(body)
    assert operation == TEST_REQUEST_OPERATION
    assert body.decode("utf-8") == "<test>Привет</test>"


def test_response_round_trip():
    message = encode_response(TEST_RESPONSE_OPERATION, "<result>OK</result>")
    operation, body = decode_response(message)

    assert message[0] == PROTOCOL_VERSION
    assert message[1] == TEST_RESPONSE_OPERATION
    assert int.from_bytes(message[2:6], "big") == len(body)
    assert operation == TEST_RESPONSE_OPERATION
    assert body.decode("utf-8") == "<result>OK</result>"


def test_request_rejects_short_header():
    with pytest.raises(ValueError):
        decode_request(b"\x01\x00")


def test_response_rejects_short_header():
    with pytest.raises(ValueError):
        decode_response(b"\x01\x07")


def test_request_rejects_invalid_version():
    message = b"\x02" + (1).to_bytes(2, "big") + (0).to_bytes(5, "big")

    with pytest.raises(ValueError):
        decode_request(message)


def test_response_rejects_invalid_body_size():
    message = b"\x01\x07" + (5).to_bytes(4, "big") + b"OK"

    with pytest.raises(ValueError):
        decode_response(message)


def test_request_rejects_invalid_operation():
    with pytest.raises(ValueError):
        encode_request(INVALID_REQUEST_OPERATION, b"")


def test_response_rejects_invalid_operation():
    with pytest.raises(ValueError):
        encode_response(INVALID_RESPONSE_OPERATION, b"")


def test_xml_value_round_trip():
    original = {
        "uid": 7,
        "platform": "Windows",
        "user_agent": "Test Browser",
    }

    element = value_to_element(original)
    restored = element_to_value(element)

    assert restored == original


def test_parse_xml_arguments():
    body = (
        b'<request>'
        b'<arg name="uid"><int>7</int></arg>'
        b'<arg name="platform"><str>Windows</str></arg>'
        b'</request>'
    )

    assert parse_arguments(body) == {
        "uid": 7,
        "platform": "Windows",
    }


def test_unknown_operation_is_rejected():
    with pytest.raises(ValueError):
        call_operation(UNKNOWN_OPERATION, {})


def test_response_contains_error():
    response = make_response(TEST_ERROR_OPERATION, error="Member not found")

    assert response[0] == PROTOCOL_VERSION
    assert response[1] == TEST_ERROR_OPERATION
    assert b"Member not found" in response


def test_tcp_client_server_round_trip():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    listener.settimeout(3)

    def serve_two_clients():
        try:
            for _ in range(2):
                connection, address = listener.accept()
                handle_connection(connection, address)
        finally:
            listener.close()

    server_thread = threading.Thread(
        target=serve_two_clients,
        daemon=True,
    )
    server_thread.start()

    client = RPCClient(port=port)
    uid = 987654321
    created = client.create_member(
        uid=uid,
        time_value=int(time.time()),
        platform="Windows",
        user_agent="Integration Test",
    )
    fetched = client.get_member(uid)

    assert created["uid"] == uid
    assert fetched["user_agent"] == "Integration Test"

    server_thread.join(timeout=3)
    assert not server_thread.is_alive()
