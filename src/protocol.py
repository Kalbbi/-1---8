
"""Кодирование и декодирование сообщений RPC-протокола."""


REQUEST_HEADER_SIZE = 8
RESPONSE_HEADER_SIZE = 6
PROTOCOL_VERSION = 1


def encode_request(operation, body):
    """Формирует RPC-запрос."""
    if not 0 <= operation <= 65535:
        raise ValueError("Код операции должен занимать 2 байта.")

    body = body.encode("utf-8") if isinstance(body, str) else body

    header = (
        PROTOCOL_VERSION.to_bytes(1, "big")
        + operation.to_bytes(2, "big")
        + len(body).to_bytes(5, "big")
    )
    return header + body


def decode_request(data):
    """Разбирает RPC-запрос."""
    if len(data) < REQUEST_HEADER_SIZE:
        raise ValueError("Заголовок запроса неполный.")

    version = data[0]
    operation = int.from_bytes(data[1:3], "big")
    body_size = int.from_bytes(data[3:8], "big")
    body = data[8:]

    if version != PROTOCOL_VERSION:
        raise ValueError("Неподдерживаемая версия протокола.")

    if len(body) != body_size:
        raise ValueError("Размер тела запроса не совпадает с заголовком.")

    return operation, body


def encode_response(operation, body):
    """Формирует RPC-ответ."""
    if not 0 <= operation <= 255:
        raise ValueError("Код операции ответа должен занимать 1 байт.")

    body = body.encode("utf-8") if isinstance(body, str) else body

    header = (
        PROTOCOL_VERSION.to_bytes(1, "big")
        + operation.to_bytes(1, "big")
        + len(body).to_bytes(4, "big")
    )
    return header + body


def decode_response(data):
    """Разбирает RPC-ответ."""
    if len(data) < RESPONSE_HEADER_SIZE:
        raise ValueError("Заголовок ответа неполный.")

    version = data[0]
    operation = data[1]
    body_size = int.from_bytes(data[2:6], "big")
    body = data[6:]

    if version != PROTOCOL_VERSION:
        raise ValueError("Неподдерживаемая версия протокола.")

    if len(body) != body_size:
        raise ValueError("Размер тела ответа не совпадает с заголовком.")

    return operation, body
