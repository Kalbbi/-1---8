
"""Тесты модели данных варианта 8."""

import pytest

from src import model


@pytest.fixture(autouse=True)
def clear_data():
    """Очищает хранилища перед каждым тестом."""
    model.members.clear()
    model.instructions.clear()
    model.outputs.clear()


def test_create_and_get_member():
    """Проверяет создание и получение Member."""
    member = model.create_member(
        1, 1000, "web", "Mozilla/5.0"
    )

    assert member["uid"] == 1
    assert model.get_member(1)["platform"] == "web"
    assert len(model.get_all_members()) == 1


def test_edit_member():
    """Проверяет редактирование Member."""
    model.create_member(1, 1000, "web", "Browser")
    updated = model.edit_member(1, {"platform": "mobile"})

    assert updated["platform"] == "mobile"
    assert updated["uid"] == 1


def test_member_errors():
    """Проверяет ошибки при работе с Member."""
    with pytest.raises(ValueError):
        model.create_member(1, 1000, "web", "Browser")
        model.create_member(1, 1000, "web", "Browser")

    with pytest.raises(KeyError):
        model.get_member(99)

    with pytest.raises(KeyError):
        model.edit_member(99, {"platform": "mobile"})


def test_create_and_get_instruction():
    """Проверяет создание и получение Instruction."""
    data = {
        "time": 1000,
        "input": "test",
        "member": 1,
        "description": "description",
        "tags": "test",
        "status": "new",
        "started": 0,
    }

    instruction = model.create_instruction(1, data)

    assert instruction["uid"] == 1
    assert model.get_instruction(1)["input"] == "test"
    assert len(model.get_all_instructions()) == 1


def test_edit_instruction():
    """Проверяет редактирование Instruction."""
    data = {
        "time": 1000,
        "input": "test",
        "member": 1,
        "description": "old",
        "tags": "test",
        "status": "new",
        "started": 0,
    }
    model.create_instruction(1, data)

    updated = model.edit_instruction(
        1, {"status": "running"}
    )

    assert updated["status"] == "running"
    assert updated["uid"] == 1


def test_create_and_get_output():
    """Проверяет создание и получение Output."""
    output = model.create_output(
        1, 1000, "response", "success", "", 1
    )

    assert output["uid"] == 1
    assert model.get_output(1)["response"] == "response"
    assert len(model.get_all_outputs()) == 1


def test_edit_output():
    """Проверяет редактирование Output."""
    model.create_output(1, 1000, "response", "success", "", 1)

    updated = model.edit_output(
        1, {"status": "failed"}
    )

    assert updated["status"] == "failed"
    assert updated["uid"] == 1


def test_output_errors():
    """Проверяет ошибки при работе с Output."""
    model.create_output(1, 1000, "response", "success", "", 1)

    with pytest.raises(ValueError):
        model.create_output(1, 1000, "response", "success", "", 1)

    with pytest.raises(KeyError):
        model.get_output(99)

    with pytest.raises(KeyError):
        model.edit_output(99, {"status": "failed"})


def test_recent_instruction_descriptions():
    """Проверяет выборку по времени, соединение и проекцию."""
    from time import time

    current_time = int(time())
    model.create_member(
        1, current_time, "web", "RecentBrowser"
    )
    model.create_member(
        2, current_time - 1000, "web", "OldBrowser"
    )

    recent_data = {
        "time": current_time,
        "input": "test",
        "member": 1,
        "description": "recent instruction",
        "tags": "test",
        "status": "new",
        "started": 0,
    }
    old_data = {
        **recent_data,
        "member": 2,
        "description": "old instruction",
    }

    model.create_instruction(1, recent_data)
    model.create_instruction(2, old_data)

    result = model.get_recent_instruction_descriptions()

    assert result == [
        {
            "description": "recent instruction",
            "user_agent": "RecentBrowser",
        }
    ]
