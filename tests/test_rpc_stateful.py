"""Stateful-тесты RPC с помощью Hypothesis."""

import socket
import threading

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    rule,
)

from src import model
from src.client import RPCClient
from src.server import handle_connection


xml_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
    ),
    max_size=30,
)


class RPCStateMachine(RuleBasedStateMachine):
    """Проверяет RPC-операции последовательностями Hypothesis."""

    def __init__(self):
        super().__init__()

        model.members.clear()
        model.instructions.clear()
        model.outputs.clear()

        self.member_ids = set()
        self.instruction_ids = set()
        self.output_ids = set()

        self.listener = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
        self.listener.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen()
        self.listener.settimeout(0.2)

        self.port = self.listener.getsockname()[1]
        self.stop_server = threading.Event()

        self.server_thread = threading.Thread(
            target=self.serve,
            daemon=True,
        )
        self.server_thread.start()

        self.client = RPCClient(port=self.port)

    def serve(self):
        """Принимает подключения тестового клиента."""
        while not self.stop_server.is_set():
            try:
                connection, address = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            handle_connection(connection, address)

    def teardown(self):
        """Останавливает тестовый сервер."""
        self.stop_server.set()
        self.listener.close()
        self.server_thread.join(timeout=2)

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        platform=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
            ),
            min_size=1,
            max_size=20,
        ),
        user_agent=xml_text,
    )
    def create_member(self, uid, time_value, platform, user_agent):
        if uid in self.member_ids:
            return

        result = self.client.create_member(
            uid,
            time_value,
            platform,
            user_agent,
        )

        self.member_ids.add(uid)

        assert result["uid"] == uid
        assert self.client.get_member(uid) == result

    @rule()
    def get_all_members(self):
        result = self.client.get_all_members()
        assert {item["uid"] for item in result} == self.member_ids

    @rule(
        platform=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
            ),
            min_size=1,
            max_size=20,
        ),
        user_agent=xml_text,
    )
    def edit_member(self, platform, user_agent):
        if not self.member_ids:
            return

        uid = min(self.member_ids)
        result = self.client.edit_member(
            uid,
            {
                "platform": platform,
                "user_agent": user_agent,
            },
        )

        assert result["uid"] == uid
        assert result["platform"] == platform
        assert result["user_agent"] == user_agent

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        fields=st.fixed_dictionaries(
            {
                "input": xml_text,
                "description": xml_text,
                "tags": xml_text,
                "status": xml_text,
                "started": st.integers(
                    min_value=0,
                    max_value=2000000000,
                ),
            }
        ),
    )
    def create_instruction(self, uid, time_value, fields):
        if uid in self.instruction_ids or not self.member_ids:
            return

        fields["time"] = time_value
        fields["member"] = min(self.member_ids)

        result = self.client.create_instruction(uid, fields)

        self.instruction_ids.add(uid)

        assert result["uid"] == uid
        assert self.client.get_instruction(uid) == result

    @rule()
    def get_all_instructions(self):
        result = self.client.get_all_instructions()
        assert {item["uid"] for item in result} == self.instruction_ids

    @rule(
        description=xml_text,
        status=xml_text,
    )
    def edit_instruction(self, description, status):
        if not self.instruction_ids:
            return

        uid = min(self.instruction_ids)
        result = self.client.edit_instruction(
            uid,
            {
                "description": description,
                "status": status,
            },
        )

        assert result["uid"] == uid
        assert result["description"] == description
        assert result["status"] == status

    @rule(
        uid=st.integers(min_value=1, max_value=1000000),
        time_value=st.integers(min_value=1, max_value=2000000000),
        response=xml_text,
        status=xml_text,
        failure=xml_text,
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

        result = self.client.create_output(
            uid,
            time_value,
            response,
            status,
            failure,
            min(self.instruction_ids),
        )

        self.output_ids.add(uid)

        assert result["uid"] == uid
        assert self.client.get_output(uid) == result

    @rule()
    def get_all_outputs(self):
        result = self.client.get_all_outputs()
        assert {item["uid"] for item in result} == self.output_ids

    @rule(
        response=xml_text,
        status=xml_text,
        failure=xml_text,
    )
    def edit_output(self, response, status, failure):
        if not self.output_ids:
            return

        uid = min(self.output_ids)
        result = self.client.edit_output(
            uid,
            {
                "response": response,
                "status": status,
                "failure": failure,
            },
        )

        assert result["uid"] == uid
        assert result["response"] == response
        assert result["status"] == status
        assert result["failure"] == failure

    @rule()
    def get_recent_instruction_descriptions(self):
        result = self.client.get_recent_instruction_descriptions()

        assert isinstance(result, list)

        for item in result:
            assert "description" in item
            assert "user_agent" in item

    @invariant()
    def identifiers_match_records(self):
        assert set(model.members) == self.member_ids
        assert set(model.instructions) == self.instruction_ids
        assert set(model.outputs) == self.output_ids


TestRPCStateMachine = RPCStateMachine.TestCase
TestRPCStateMachine.settings = settings(
    max_examples=30,
    stateful_step_count=30,
    deadline=None,
)
