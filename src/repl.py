"""Интерактивная консоль для работы с моделью данных."""

from src import model


def show_help():
    """Показывает доступные команды."""
    commands = [
        "create_member",
        "get_all_members",
        "get_member",
        "edit_member",
        "create_instruction",
        "get_all_instructions",
        "get_instruction",
        "edit_instruction",
        "create_output",
        "get_all_outputs",
        "get_output",
        "edit_output",
        "recent",
        "help",
        "exit",
    ]
    print("Доступные команды:")
    for command in commands:
        print(command)


def read_member_data():
    """Считывает данные участника."""
    return {
        "uid": int(input("uid: ")),
        "time": int(input("time: ")),
        "platform": input("platform: "),
        "user_agent": input("user_agent: "),
    }


def read_instruction_data():
    """Считывает данные инструкции."""
    return {
        "uid": int(input("uid: ")),
        "time": int(input("time: ")),
        "input": input("input: "),
        "member": int(input("member: ")),
        "description": input("description: "),
        "tags": input("tags: "),
        "status": input("status: "),
        "started": int(input("started: ")),
    }


def read_output_data():
    """Считывает данные результата."""
    return {
        "uid": int(input("uid: ")),
        "time": int(input("time: ")),
        "response": input("response: "),
        "status": input("status: "),
        "failure": input("failure: "),
        "instruction": int(input("instruction: ")),
    }


def create_member():
    """Создаёт участника."""
    data = read_member_data()
    return model.create_member(
        data["uid"],
        data["time"],
        data["platform"],
        data["user_agent"],
    )


def create_instruction():
    """Создаёт инструкцию."""
    data = read_instruction_data()
    uid = data.pop("uid")
    return model.create_instruction(uid, data)


def create_output():
    """Создаёт результат выполнения инструкции."""
    data = read_output_data()
    return model.create_output(
        data["uid"],
        data["time"],
        data["response"],
        data["status"],
        data["failure"],
        data["instruction"],
    )


def edit_member():
    """Изменяет данные участника."""
    uid = int(input("uid: "))
    data = {
        "platform": input("platform: "),
        "user_agent": input("user_agent: "),
    }
    return model.edit_member(uid, data)


def edit_instruction():
    """Изменяет данные инструкции."""
    uid = int(input("uid: "))
    data = {
        "status": input("status: "),
        "description": input("description: "),
    }
    return model.edit_instruction(uid, data)


def edit_output():
    """Изменяет данные результата."""
    uid = int(input("uid: "))
    data = {
        "response": input("response: "),
        "status": input("status: "),
        "failure": input("failure: "),
    }
    return model.edit_output(uid, data)


def execute_single_getter(command, single_getters):
    """Получает одну запись по идентификатору."""
    try:
        uid = int(input("uid: "))
    except ValueError:
        print("Ошибка: uid должен быть целым числом.")
        return

    print(single_getters[command](uid))


def execute_command(command):
    """Выполняет команду консоли."""
    handlers = {
        "create_member": create_member,
        "create_instruction": create_instruction,
        "create_output": create_output,
        "edit_member": edit_member,
        "edit_instruction": edit_instruction,
        "edit_output": edit_output,
    }

    if command in handlers:
        print(handlers[command]())
        return

    getters = {
        "get_all_members": model.get_all_members,
        "get_all_instructions": model.get_all_instructions,
        "get_all_outputs": model.get_all_outputs,
        "recent": model.get_recent_instruction_descriptions,
    }

    if command in getters:
        print(getters[command]())
        return

    single_getters = {
        "get_member": model.get_member,
        "get_instruction": model.get_instruction,
        "get_output": model.get_output,
    }

    if command in single_getters:
        execute_single_getter(command, single_getters)
        return

    print("Неизвестная команда. Введите help.")


def run_repl():
    """Запускает интерактивную консоль."""
    print("REPL модели данных.")
    print("Введите help для списка команд.")

    while True:
        command = input(">>> ").strip()

        if command == "exit":
            print("Выход.")
            break

        if command == "help":
            show_help()
            continue

        try:
            execute_command(command)
        except (ValueError, KeyError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    run_repl()
