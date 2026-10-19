"""TCP-сервер для обработки RPC-запросов."""

import socket
import xml.etree.ElementTree as element_tree

from src import model
from src.protocol import (
    REQUEST_HEADER_SIZE,
    decode_request,
    encode_response,
)


HOST = "127.0.0.1"
PORT = 5000


OPERATIONS = {
    1: "create_member",
    2: "get_all_members",
    3: "get_member",
    4: "edit_member",
    5: "create_instruction",
    6: "get_all_instructions",
    7: "get_instruction",
    8: "edit_instruction",
    9: "create_output",
    10: "get_all_outputs",
    11: "get_output",
    12: "edit_output",
    13: "get_recent_instruction_descriptions",
}


def read_exact(connection, size):
    """Читает заданное количество байтов из TCP-соединения."""
    chunks = []
    remaining = size

    while remaining > 0:
        chunk = connection.recv(remaining)
        if not chunk:
            raise ConnectionError("Соединение закрыто до получения данных.")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def read_request(connection):
    """Читает один полный RPC-запрос."""
    header = read_exact(connection, REQUEST_HEADER_SIZE)
    body_size = int.from_bytes(header[3:8], "big")
    body = read_exact(connection, body_size)
    return decode_request(header + body)


def _dict_to_value(element):
    """Преобразует XML-словарь в Python-словарь."""
    result = {}
    for child in element:
        key = child.get("key")
        if key is None:
            key = child.get("name", child.tag)
        result[key] = element_to_value(child[0])
    return result


def element_to_value(element):
    """Преобразует XML-элемент в Python-значение."""
    converters = {
        "none": lambda item: None,
        "bool": lambda item: item.text == "true",
        "int": lambda item: int(item.text),
        "str": lambda item: item.text or "",
        "list": lambda item: [
            element_to_value(child) for child in item
        ],
        "dict": _dict_to_value,
    }

    converter = converters.get(element.tag)
    if converter is None:
        raise ValueError(
            f"Неизвестный XML-тип: {element.tag}"
        )
    return converter(element)


def value_to_element(value, tag="value"):
    """Преобразует Python-значение в XML-элемент."""
    if value is None:
        element = element_tree.Element("none")
    elif isinstance(value, bool):
        element = element_tree.Element("bool")
        element.text = "true" if value else "false"
    elif isinstance(value, int):
        element = element_tree.Element("int")
        element.text = str(value)
    elif isinstance(value, str):
        element = element_tree.Element("str")
        element.text = value
    elif isinstance(value, (list, tuple)):
        element = element_tree.Element("list")
        for item in value:
            element.append(value_to_element(item, "item"))
    elif isinstance(value, dict):
        element = element_tree.Element("dict")
        for key, item in value.items():
            child = element_tree.SubElement(element, "item", key=str(key))
            child.append(value_to_element(item))
    else:
        raise ValueError(f"Неподдерживаемый тип: {type(value).__name__}")

    element.set("name", tag)
    return element


def parse_arguments(body):
    """Извлекает именованные аргументы из XML-тела запроса."""
    root = element_tree.fromstring(body)
    arguments = {}

    for child in root:
        name = child.get("name")

        if child.tag == "arg":
            if name is None or len(child) != 1:
                raise ValueError("Некорректный XML-аргумент.")
            arguments[name] = element_to_value(child[0])
        else:
            if name is None:
                raise ValueError("У аргумента отсутствует имя.")
            arguments[name] = element_to_value(child)

    return arguments


def _create_operation(name, arguments):
    """Обрабатывает RPC-операции создания записей."""
    if name == "create_member":
        return model.create_member(
            arguments["uid"],
            arguments["time"],
            arguments["platform"],
            arguments["user_agent"],
        )

    if name == "create_instruction":
        uid = arguments.pop("uid")
        return model.create_instruction(uid, arguments)

    if name == "create_output":
        return model.create_output(
            arguments["uid"],
            arguments["time"],
            arguments["response"],
            arguments["status"],
            arguments["failure"],
            arguments["instruction"],
        )

    raise ValueError("Неизвестная операция создания.")


def call_operation(operation, arguments):
    """Вызывает функцию модели по коду RPC-операции."""
    if operation not in OPERATIONS:
        raise ValueError("Неизвестный код операции.")

    name = OPERATIONS[operation]
    if name.startswith("create_"):
        return _create_operation(name, arguments)

    if name in {
        "get_all_members",
        "get_all_instructions",
        "get_all_outputs",
        "get_recent_instruction_descriptions",
    }:
        return getattr(model, name)()

    if name in {"get_member", "get_instruction", "get_output"}:
        return getattr(model, name)(arguments["uid"])

    if name in {"edit_member", "edit_instruction", "edit_output"}:
        uid = arguments.pop("uid")
        return getattr(model, name)(uid, arguments)

    raise ValueError("Операция не реализована.")


def make_response(operation, result=None, error=None):
    """Формирует XML-ответ с результатом или ошибкой."""
    root = element_tree.Element("response")

    if error is None:
        root.append(value_to_element(result, "result"))
        root.set("status", "ok")
    else:
        root.set("status", "error")
        message = element_tree.SubElement(root, "error")
        message.text = str(error)

    body = element_tree.tostring(root, encoding="utf-8")
    return encode_response(operation % 256, body)


def handle_connection(connection, address):
    """Обрабатывает RPC-запросы одного клиента."""
    with connection:
        while True:
            try:
                operation, body = read_request(connection)
            except ConnectionError:
                break
            except ValueError as error:
                print(f"Ошибка запроса от {address}: {error}")
                break

            print(
                f"RPC-запрос от {address}: "
                f"операция={operation}, "
                f"тело={body.decode('utf-8', errors='replace')}"
            )

            try:
                arguments = parse_arguments(body)
                result = call_operation(operation, arguments)
                response = make_response(operation, result=result)
            except (
                KeyError,
                ValueError,
                TypeError,
                element_tree.ParseError,
            ) as error:
                response = make_response(operation, error=error)

            connection.sendall(response)


def run_server():
    """Запускает TCP-сервер."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print("RPC-сервер запущен на {}:{}".format(HOST, PORT))

        while True:
            connection, address = server.accept()
            handle_connection(connection, address)


if __name__ == "__main__":
    run_server()
