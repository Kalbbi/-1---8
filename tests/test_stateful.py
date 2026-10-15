"""Stateful-тесты модели данных с помощью Hypothesis."""

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    rule,
)

from src import model


class ModelStateMachine(RuleBasedStateMachine):
    """Проверяет модель данных после последовательностей операций."""

    def __init__(self):
        super().__init__()
        model.members.clear()
        model.instructions.clear()
        model.outputs.clear()

        self.member_ids = set()
        self.instruction_ids = set()
        self.output_ids = set()

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        platform=st.text(min_size=1, max_size=20),
        user_agent=st.text(max_size=50),
    )
    def create_member(self, uid, time_value, platform, user_agent):
        if uid in self.member_ids:
            return

        created = model.create_member(
            uid,
            time_value,
            platform,
            user_agent,
        )
        self.member_ids.add(uid)

        assert created["uid"] == uid
        assert model.get_member(uid) == created

    @rule()
    def get_all_members(self):
        result = model.get_all_members()

        assert len(result) == len(self.member_ids)
        assert {member["uid"] for member in result} == self.member_ids

    @rule(
        platform=st.text(min_size=1, max_size=20),
        user_agent=st.text(max_size=50),
    )
    def edit_member(self, platform, user_agent):
        if not self.member_ids:
            return

        uid = min(self.member_ids)
        updated = model.edit_member(
            uid,
            {
                "platform": platform,
                "user_agent": user_agent,
            },
        )

        assert updated["uid"] == uid
        assert model.get_member(uid) == updated

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        input_value=st.text(max_size=50),
        description=st.text(max_size=50),
        tags=st.text(max_size=30),
        status=st.text(max_size=20),
        started=st.integers(min_value=0, max_value=2000000000),
    )
    def create_instruction(
        self,
        uid,
        time_value,
        input_value,
        description,
        tags,
        status,
        started,
    ):
        if uid in self.instruction_ids or not self.member_ids:
            return

        member_uid = min(self.member_ids)
        created = model.create_instruction(
            uid,
            {
                "time": time_value,
                "input": input_value,
                "member": member_uid,
                "description": description,
                "tags": tags,
                "status": status,
                "started": started,
            },
        )
        self.instruction_ids.add(uid)

        assert created["uid"] == uid
        assert model.get_instruction(uid) == created

    @rule()
    def get_all_instructions(self):
        result = model.get_all_instructions()

        assert len(result) == len(self.instruction_ids)
        assert {
            instruction["uid"] for instruction in result
        } == self.instruction_ids

    @rule(
        description=st.text(max_size=50),
        status=st.text(max_size=20),
    )
    def edit_instruction(self, description, status):
        if not self.instruction_ids:
            return

        uid = min(self.instruction_ids)
        updated = model.edit_instruction(
            uid,
            {
                "description": description,
                "status": status,
            },
        )

        assert updated["uid"] == uid
        assert model.get_instruction(uid) == updated

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        response=st.text(max_size=50),
        status=st.text(max_size=20),
        failure=st.text(max_size=50),
    )
    def create_output(
        self,
        uid,
        time_value,
        response,
        status,
        failure,
    ):
        if uid in self.output_ids or not self.instruction_ids:
            return

        instruction_uid = min(self.instruction_ids)
        created = model.create_output(
            uid,
            time_value,
            response,
            status,
            failure,
            instruction_uid,
        )
        self.output_ids.add(uid)

        assert created["uid"] == uid
        assert model.get_output(uid) == created

    @rule()
    def get_all_outputs(self):
        result = model.get_all_outputs()

        assert len(result) == len(self.output_ids)
        assert {output["uid"] for output in result} == self.output_ids

    @rule(
        response=st.text(max_size=50),
        status=st.text(max_size=20),
        failure=st.text(max_size=50),
    )
    def edit_output(self, response, status, failure):
        if not self.output_ids:
            return

        uid = min(self.output_ids)
        updated = model.edit_output(
            uid,
            {
                "response": response,
                "status": status,
                "failure": failure,
            },
        )

        assert updated["uid"] == uid
        assert model.get_output(uid) == updated

    @rule()
    def get_recent_instruction_descriptions(self):
        result = model.get_recent_instruction_descriptions()

        assert isinstance(result, list)

        for item in result:
            assert "description" in item
            assert "user_agent" in item

    @invariant()
    def identifiers_match_records(self):
        assert set(model.members) == self.member_ids
        assert set(model.instructions) == self.instruction_ids
        assert set(model.outputs) == self.output_ids


TestModelStateMachine = ModelStateMachine.TestCase
TestModelStateMachine.settings = settings(
    max_examples=30,
    stateful_step_count=20,
    deadline=None,
)
