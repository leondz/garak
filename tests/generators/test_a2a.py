# SPDX-FileCopyrightText: Portions Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import pytest

from garak.attempt import Conversation, Message, Turn
from garak.exception import APIKeyMissingError
from garak.generators.a2a import A2AGenerator

URI = "https://agent.example/a2a"


@pytest.fixture
def sample_conversation():
    conv = Conversation()
    conv.turns.append(Turn("user", Message(text="Test probe prompt")))
    return conv


@pytest.fixture(autouse=True)
def clear_a2a_env(monkeypatch):
    monkeypatch.delenv("A2A_API_KEY", raising=False)


def _response(payload):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


def test_a2a_initialization():
    gen = A2AGenerator(name=URI)
    assert gen.uri == URI
    assert gen.generator_family_name == "A2A"
    assert gen.dialect == "auto"
    assert gen.api_key is None


def test_a2a_requires_uri():
    with pytest.raises(ValueError):
        A2AGenerator()


def test_a2a_rejects_unknown_dialect():
    gen_config = {"a2a": {"A2AGenerator": {"uri": URI, "dialect": "v9"}}}
    from garak._config import GarakSubConfig

    config_root = GarakSubConfig()
    setattr(config_root, "generators", gen_config)
    with pytest.raises(ValueError):
        A2AGenerator(config_root=config_root)


def test_a2a_env_api_key(monkeypatch):
    monkeypatch.setenv("A2A_API_KEY", "env-secret")
    gen = A2AGenerator(name=URI)
    assert gen.api_key == "env-secret"
    assert gen._build_headers()["X-API-Key"] == "env-secret"


def test_a2a_custom_env_var_required():
    from garak._config import GarakSubConfig

    config_root = GarakSubConfig()
    setattr(
        config_root,
        "generators",
        {"a2a": {"A2AGenerator": {"uri": URI, "key_env_var": "MY_A2A_KEY"}}},
    )
    with pytest.raises(APIKeyMissingError):
        A2AGenerator(config_root=config_root)


@patch("requests.post")
def test_a2a_v03_success(mock_post, sample_conversation):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "kind": "task",
                "id": "task-100",
                "contextId": "ctx-1",
                "status": {"state": "completed"},
                "artifacts": [
                    {"parts": [{"kind": "text", "text": "Agent response text"}]}
                ],
            },
        }
    )

    gen = A2AGenerator(name=URI)
    results = gen._call_model(prompt=sample_conversation)

    assert len(results) == 1
    assert isinstance(results[0], Message)
    assert results[0].text == "Agent response text"
    assert gen.dialect == "v03"

    call_payload = mock_post.call_args.kwargs["json"]
    assert call_payload["method"] == "message/send"
    message = call_payload["params"]["message"]
    assert message["kind"] == "message"
    assert message["messageId"]
    assert message["parts"] == [
        {"kind": "text", "text": "Test probe prompt", "metadata": {"role": "user"}}
    ]


@patch("requests.post")
def test_a2a_message_result(mock_post, sample_conversation):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "kind": "message",
                "role": "agent",
                "messageId": "m-1",
                "parts": [{"kind": "text", "text": "Direct reply"}],
            },
        }
    )

    gen = A2AGenerator(name=URI)
    assert gen._call_model(prompt=sample_conversation)[0].text == "Direct reply"


@patch("requests.post")
def test_a2a_multi_turn_conversation(mock_post):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {"parts": [{"kind": "text", "text": "ok"}]},
        }
    )
    conv = Conversation(
        [
            Turn("system", Message(text="You are a helpful agent.")),
            Turn("user", Message(text="First question")),
            Turn("assistant", Message(text="First answer")),
            Turn("user", Message(text="Follow up")),
        ]
    )

    gen = A2AGenerator(name=URI)
    gen._call_model(prompt=conv)

    parts = mock_post.call_args.kwargs["json"]["params"]["message"]["parts"]
    assert [p["metadata"]["role"] for p in parts] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert [p["text"] for p in parts] == [
        "System: You are a helpful agent.",
        "User: First question",
        "Assistant: First answer",
        "Follow up",
    ]


@patch("requests.post")
def test_a2a_calls_are_independent(mock_post, sample_conversation):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "id": "task-1",
                "contextId": "ctx-1",
                "artifacts": [{"parts": [{"kind": "text", "text": "ok"}]}],
            },
        }
    )

    gen = A2AGenerator(name=URI)
    gen._call_model(prompt=sample_conversation)
    gen._call_model(prompt=sample_conversation)

    for call in mock_post.call_args_list:
        message = call.kwargs["json"]["params"]["message"]
        assert "taskId" not in message
        assert "contextId" not in message


@patch("requests.post")
def test_a2a_fallback_to_v02(mock_post, sample_conversation):
    resp_err = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "error": {"code": -32601, "message": "Method not found"},
        }
    )
    resp_v02 = _response(
        {
            "jsonrpc": "2.0",
            "id": "2",
            "result": {
                "id": "task-v02-id",
                "status": {
                    "state": "completed",
                    "message": {
                        "role": "agent",
                        "parts": [{"type": "text", "text": "Legacy 0.2 reply"}],
                    },
                },
            },
        }
    )
    mock_post.side_effect = [resp_err, resp_v02]

    gen = A2AGenerator(name=URI)
    results = gen._call_model(prompt=sample_conversation)

    assert len(results) == 1
    assert results[0].text == "Legacy 0.2 reply"
    assert gen.dialect == "v02"
    assert mock_post.call_count == 2

    retry_payload = mock_post.call_args_list[1].kwargs["json"]
    assert retry_payload["method"] == "tasks/send"
    assert retry_payload["params"]["message"]["parts"][0]["type"] == "text"


@patch("requests.post")
def test_a2a_rpc_error_is_no_output(mock_post, sample_conversation):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "error": {"code": -32000, "message": "Internal error"},
        }
    )

    gen = A2AGenerator(name=URI)
    results = gen._call_model(prompt=sample_conversation)

    assert results == [None]
    assert gen.dialect == "auto"


@patch("requests.post")
def test_a2a_auth_headers(mock_post, sample_conversation):
    mock_post.return_value = _response(
        {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {"parts": [{"kind": "text", "text": "Authed"}]},
        }
    )

    gen = A2AGenerator(name=URI)
    gen.auth_token = "bearer-secret-token"
    gen._call_model(prompt=sample_conversation)

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer bearer-secret-token"
