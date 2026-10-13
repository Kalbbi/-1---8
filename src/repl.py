"""Интерактивная консоль для работы с моделью данных."""

from src import model


def show_help():
    """Показывает доступные команды."""
    print("Доступные команды:")
    print("create_member")
    print("get_all_members")
    print("get_member")
    print("edit_member")
    print("create_instruction")
    print("get_all_instructions")
    print("get_instruction")
    print("edit_instruction")
    print("create_output")
    print("get_all_outputs")
    print("get_output")
    print("edit_output")
    print("recent")
    print("help")
    print("exit")


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

        if command == "get_all_members":
            print(model.get_all_members())
            continue

        if command == "get_member":
            uid = int(input("uid: "))
            try:
                print(model.get_member(uid))
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "edit_member":
            uid = int(input("uid: "))
            platform = input("platform: ")
            user_agent = input("user_agent: ")

            try:
                member = model.edit_member(
                    uid,
                    {
                        "platform": platform,
                        "user_agent": user_agent,
                    },
                )
                print(member)
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "create_member":
            uid = int(input("uid: "))
            time_value = int(input("time: "))
            platform = input("platform: ")
            user_agent = input("user_agent: ")

            try:
                member = model.create_member(
                    uid,
                    time_value,
                    platform,
                    user_agent,
                )
                print(member)
            except (ValueError, KeyError) as error:
                print(f"Ошибка: {error}")
            continue

        if command == "create_instruction":
            uid = int(input("uid: "))
            time_value = int(input("time: "))
            input_value = input("input: ")
            member = int(input("member: "))
            description = input("description: ")
            tags = input("tags: ")
            status = input("status: ")
            started = int(input("started: "))

            try:
                instruction = model.create_instruction(
                    uid,
                    {
                        "time": time_value,
                        "input": input_value,
                        "member": member,
                        "description": description,
                        "tags": tags,
                        "status": status,
                        "started": started,
                    },
                )
                print(instruction)
            except (ValueError, KeyError) as error:
                print(f"Ошибка: {error}")
            continue

        if command == "get_all_instructions":
            print(model.get_all_instructions())
            continue

        if command == "get_instruction":
            uid = int(input("uid: "))
            try:
                print(model.get_instruction(uid))
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "edit_instruction":
            uid = int(input("uid: "))
            status = input("status: ")
            description = input("description: ")

            try:
                instruction = model.edit_instruction(
                    uid,
                    {
                        "status": status,
                        "description": description,
                    },
                )
                print(instruction)
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "create_output":
            uid = int(input("uid: "))
            time_value = int(input("time: "))
            response = input("response: ")
            status = input("status: ")
            failure = input("failure: ")
            instruction = int(input("instruction: "))

            output = model.create_output(
                uid,
                time_value,
                response,
                status,
                failure,
                instruction,
            )
            print(output)
            continue

        if command == "get_all_outputs":
            print(model.get_all_outputs())
            continue

        if command == "get_output":
            uid = int(input("uid: "))
            try:
                print(model.get_output(uid))
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "edit_output":
            uid = int(input("uid: "))
            response = input("response: ")
            status = input("status: ")
            failure = input("failure: ")

            try:
                output = model.edit_output(
                    uid,
                    {
                        "response": response,
                        "status": status,
                        "failure": failure,
                    },
                )
                print(output)
            except KeyError as error:
                print(f"Ошибка: {error}")
            continue

        if command == "recent":
            print(model.get_recent_instruction_descriptions())
            continue

        print("Команда пока не реализована.")


if __name__ == "__main__":
    run_repl()
