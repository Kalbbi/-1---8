"""TCP-клиент для выполнения RPC-операций."""

import socket
import xml.etree.ElementTree as element_tree

from src.protocol import (
    RESPONSE_HEADER_SIZE,
    decode_response,
    encode_request,
)


HOST = "127.0.0.1"
PORT = 5000


def value_to_element(value, name="value"):
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

    element.set("name", name)
    return element


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


def read_exact(connection, size):
    """Читает заданное количество байтов."""
    chunks = []
    remaining = size

    while remaining > 0:
        chunk = connection.recv(remaining)
        if not chunk:
            raise ConnectionError("Сервер закрыл соединение.")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


class RPCClient:
    """Клиент для выполнения удалённых процедур."""

    def __init__(self, host=HOST, port=PORT, timeout=5):
        """Сохраняет параметры подключения."""
        self.host = host
        self.port = port
        self.timeout = timeout

    def _make_request(self, operation, arguments):
        """Формирует XML и кодирует RPC-запрос."""
        root = element_tree.Element("request")
        for name, value in arguments.items():
            root.append(value_to_element(value, name))
        body = element_tree.tostring(root, encoding="utf-8")
        return encode_request(operation, body)

    def _exchange(self, request):
        """Отправляет запрос и получает ответ по TCP."""
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout,
        ) as connection:
            connection.sendall(request)
            header = read_exact(connection, RESPONSE_HEADER_SIZE)
            body_size = int.from_bytes(header[2:6], "big")
            response_body = read_exact(connection, body_size)
        return header + response_body

    def _parse_response(self, operation, response_data):
        """Проверяет и разбирает ответ сервера."""
        response_operation, response_xml = decode_response(response_data)
        if response_operation != operation % 256:
            raise ValueError("Код операции в ответе не совпадает с запросом.")

        response = element_tree.fromstring(response_xml)
        if response.get("status") == "error":
            error = response.findtext("error", "Неизвестная ошибка")
            raise RuntimeError(error)

        result = next(
            (
                child
                for child in response
                if child.get("name") == "result"
            ),
            None,
        )
        return None if result is None else element_to_value(result)

    def call(self, operation, arguments=None):
        """Отправляет запрос и возвращает результат сервера."""
        request = self._make_request(operation, arguments or {})
        response_data = self._exchange(request)
        return self._parse_response(operation, response_data)

    def create_member(
        self, uid, time_value, platform, user_agent
    ):
        """Создаёт участника."""
        return self.call(
            1,
            {
                "uid": uid,
                "time": time_value,
                "platform": platform,
                "user_agent": user_agent,
            },
        )

    def get_all_members(self):
        """Возвращает всех участников."""
        return self.call(2)

    def get_member(self, uid):
        """Возвращает участника по идентификатору."""
        return self.call(3, {"uid": uid})

    def edit_member(self, uid, data):
        """Изменяет данные участника."""
        return self.call(4, {"uid": uid, **data})

    def create_instruction(self, uid, data):
        """Создаёт инструкцию."""
        return self.call(5, {"uid": uid, **data})

    def get_all_instructions(self):
        """Возвращает все инструкции."""
        return self.call(6)

    def get_instruction(self, uid):
        """Возвращает инструкцию по идентификатору."""
        return self.call(7, {"uid": uid})

    def edit_instruction(self, uid, data):
        """Изменяет инструкцию."""
        return self.call(8, {"uid": uid, **data})

    def create_output(
        self,
        uid,
        time_value,
        response,
        status,
        failure,
        instruction,
    ):
        """Создаёт результат выполнения инструкции."""
        return self.call(
            9,
            {
                "uid": uid,
                "time": time_value,
                "response": response,
                "status": status,
                "failure": failure,
                "instruction": instruction,
            },
        )

    def get_all_outputs(self):
        """Возвращает все результаты."""
        return self.call(10)

    def get_output(self, uid):
        """Возвращает результат по идентификатору."""
        return self.call(11, {"uid": uid})

    def edit_output(self, uid, data):
        """Изменяет результат."""
        return self.call(12, {"uid": uid, **data})

    def get_recent_instruction_descriptions(self):
        """Возвращает описания недавних инструкций."""
        return self.call(13)
