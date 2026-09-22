# SPDX-FileCopyrightText: Portions Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import pytest

from garak.attempt import Conversation, Message, Turn
from garak.generators.a2a import A2AGenerator


@pytest.fixture
def sample_conversation():
    conv = Conversation()
    conv.turns.append(Turn("user", Message(text="Test probe prompt")))
    return conv


def test_a2a_initialization():
    gen = A2AGenerator(name="https://agent.example/a2a")
    assert gen.uri == "https://agent.example/a2a"
    assert gen.generator_family_name == "A2A"
    assert gen.dialect == "auto"


@patch("requests.post")
def test_a2a_v03_success(mock_post, sample_conversation):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "taskId": "task-100",
            "message": {
                "role": "assistant",
                "parts": [{"kind": "text", "text": "Agent response text"}],
            },
        },
    }
    mock_post.return_value = mock_resp

    gen = A2AGenerator(name="https://agent.example/a2a")
    results = gen._call_model(prompt=sample_conversation)

    assert len(results) == 1
    assert isinstance(results[0], Message)
    assert results[0].text == "Agent response text"
    assert gen.task_id == "task-100"
    assert gen.dialect == "v03"

    call_payload = mock_post.call_args.kwargs["json"]
    assert call_payload["method"] == "message/send"
    assert call_payload["params"]["message"]["parts"][0]["kind"] == "text"


@patch("requests.post")
def test_a2a_fallback_to_v02(mock_post, sample_conversation):
    resp_err = MagicMock()
    resp_err.status_code = 200
    resp_err.json.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "error": {"code": -32601, "message": "Method not found"},
    }

    resp_v02 = MagicMock()
    resp_v02.status_code = 200
    resp_v02.json.return_value = {
        "jsonrpc": "2.0",
        "id": "2",
        "result": {
            "id": "task-v02-id",
            "message": {
                "role": "assistant",
                "parts": [{"type": "text", "text": "Legacy 0.2 reply"}],
            },
        },
    }
    mock_post.side_effect = [resp_err, resp_v02]

    gen = A2AGenerator(name="https://agent.example/a2a")
    results = gen._call_model(prompt=sample_conversation)

    assert len(results) == 1
    assert results[0].text == "Legacy 0.2 reply"
    assert gen.dialect == "v02"
    assert mock_post.call_count == 2

    retry_payload = mock_post.call_args_list[1].kwargs["json"]
    assert retry_payload["method"] == "tasks/send"
    assert retry_payload["params"]["message"]["parts"][0]["type"] == "text"


@patch("requests.post")
def test_a2a_refusal_extracted(mock_post, sample_conversation):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "error": {
            "code": -32000,
            "message": "I cannot fulfill this request due to safety policies.",
        },
    }
    mock_post.return_value = mock_resp

    gen = A2AGenerator(name="https://agent.example/a2a")
    results = gen._call_model(prompt=sample_conversation)

    assert len(results) == 1
    assert results[0].text == "[A2A Refusal] I cannot fulfill this request due to safety policies."


@patch("requests.post")
def test_a2a_auth_headers(mock_post, sample_conversation):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {"message": {"parts": [{"kind": "text", "text": "Authed"}]}},
    }
    mock_post.return_value = mock_resp

    gen = A2AGenerator(name="https://agent.example/a2a")
    gen.auth_token = "bearer-secret-token"
    gen._call_model(prompt=sample_conversation)

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer bearer-secret-token"


@patch("requests.get")
def test_a2a_agent_card(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"name": "SecurityAgent", "skills": []}
    mock_get.return_value = mock_resp

    gen = A2AGenerator(name="https://agent.example/a2a/tasks")
    card = gen.get_agent_card()

    assert card["name"] == "SecurityAgent"
    assert mock_get.call_args[0][0] == "https://agent.example/.well-known/agent-card.json"
