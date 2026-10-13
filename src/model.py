"""Модель данных варианта 8."""

from time import time

members = {}
instructions = {}
outputs = {}

def create_member(
    uid,
    time_value,
    platform,
    user_agent,
):
    """Создаёт новую запись Member."""
    if uid in members:
        raise ValueError("Member with this uid already exists")

    members[uid] = {
        "uid": uid,
        "time": time_value,
        "platform": platform,
        "user_agent": user_agent,
    }
    return members[uid]


def get_all_members():
    """Возвращает все записи Member."""
    return list(members.values())


def get_member(uid):
    """Возвращает запись Member по идентификатору."""
    if uid not in members:
        raise KeyError("Member not found")

    return members[uid]


def edit_member(uid, data):
    """Редактирует запись Member."""
    if uid not in members:
        raise KeyError("Member not found")

    members[uid].update(data)
    members[uid]["uid"] = uid
    return members[uid]

def create_instruction(uid, data):
    """Создаёт новую запись Instruction."""
    if uid in instructions:
        raise ValueError("Instruction with this uid already exists")

    instructions[uid] = {
        "uid": uid,
        "time": data["time"],
        "input": data["input"],
        "member": data["member"],
        "description": data["description"],
        "tags": data["tags"],
        "status": data["status"],
        "started": data["started"],
    }
    return instructions[uid]


def get_all_instructions():
    """Возвращает все записи Instruction."""
    return list(instructions.values())


def get_instruction(uid):
    """Возвращает Instruction по идентификатору."""
    if uid not in instructions:
        raise KeyError("Instruction not found")

    return instructions[uid]


def edit_instruction(uid, data):
    """Редактирует запись Instruction."""
    if uid not in instructions:
        raise KeyError("Instruction not found")

    instructions[uid].update(data)
    instructions[uid]["uid"] = uid
    return instructions[uid]

def create_output(
    uid,
    time_value,
    response,
    status,
    failure,
    instruction,
):
    """Создаёт новую запись Output."""
    if uid in outputs:
        raise ValueError("Output with this uid already exists")

    outputs[uid] = {
        "uid": uid,
        "time": time_value,
        "response": response,
        "status": status,
        "failure": failure,
        "instruction": instruction,
    }
    return outputs[uid]


def get_all_outputs():
    """Возвращает все записи Output."""
    return list(outputs.values())


def get_output(uid):
    """Возвращает Output по идентификатору."""
    if uid not in outputs:
        raise KeyError("Output not found")

    return outputs[uid]


def edit_output(uid, data):
    """Редактирует запись Output."""
    if uid not in outputs:
        raise KeyError("Output not found")

    outputs[uid].update(data)
    outputs[uid]["uid"] = uid
    return outputs[uid]


def get_recent_instruction_descriptions():
    """Возвращает описания инструкций и user_agent за последние 9 минут."""
    current_time = int(time())
    threshold = current_time - 9 * 60
    result = []

    for member in members.values():
        if member["time"] <= threshold:
            continue

        for instruction in instructions.values():
            if instruction["member"] != member["uid"]:
                continue

            result.append(
                {
                    "description": instruction["description"],
                    "user_agent": member["user_agent"],
                }
            )

    return result