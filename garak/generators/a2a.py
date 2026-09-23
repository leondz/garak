# SPDX-FileCopyrightText: Portions Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""A2A (Agent-to-Agent) Generator

Generator module for probing agents exposing the Agent-to-Agent protocol over JSON-RPC.
"""

import logging
import uuid
from typing import ClassVar, List, Union
from urllib.parse import urljoin

import requests

from garak import _config
from garak.attempt import Conversation, Message
from garak.exception import BadGeneratorException
from garak.generators.base import Generator

logger = logging.getLogger(__name__)

RPC_METHOD_NOT_FOUND = -32601


class A2AGenerator(Generator):
    """Generic Generator for Agent-to-Agent (A2A) protocol endpoints.

    Communicates with agents implementing task-based message exchange over JSON-RPC 2.0.
    Natively negotiates between:
    - Spec 0.3+ (`message/send` with `kind: "text"`)
    - Spec 0.2 (`tasks/send` with `type: "text"`)

    Automatically falls back from 0.3 to 0.2 when encountering error code -32601 (Method not found).
    Maintains session task ID across multi-turn probe conversations.
    """

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "uri": "",
        "api_key": None,
        "api_key_header": "X-API-Key",
        "auth_token": None,
        "request_timeout": 30,
        "verify_ssl": True,
        "dialect": "auto",
    }

    _supported_params = (
        "name",
        "uri",
        "api_key",
        "api_key_header",
        "auth_token",
        "request_timeout",
        "verify_ssl",
        "dialect",
        "max_tokens",
        "temperature",
        "top_k",
        "context_len",
        "skip_seq_start",
        "skip_seq_end",
    )

    ENV_VAR = "A2A_API_KEY"
    generator_family_name = "A2A"
    active = True
    modality: ClassVar[dict] = {"in": {"text"}, "out": {"text"}}

    def __init__(self, name="", config_root=_config):
        self.uri = ""
        self.name = name
        self.api_key = None
        self.api_key_header = "X-API-Key"
        self.auth_token = None
        self.request_timeout = 30
        self.verify_ssl = True
        self.dialect = "auto"
        self.task_id = None

        super().__init__(name, config_root=config_root)
        if not self.uri and self.name and self.name.startswith(("http://", "https://")):
            self.uri = self.name

    def _validate_env_var(self):
        """API key is optional for A2A endpoints (may use Bearer tokens or no auth)."""

    def clear_history(self):
        """Reset conversation session task tracking."""
        self.task_id = None

    def _build_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers[self.api_key_header] = self.api_key
        return headers

    def _build_payload(self, dialect: str, message_text: str) -> dict:
        rpc_id = str(uuid.uuid4())
        if dialect == "v03":
            params = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": message_text}],
                }
            }
            if self.task_id:
                params["task_id"] = self.task_id
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "method": "message/send",
                "params": params,
            }
        effective_id = self.task_id or str(uuid.uuid4())
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": "tasks/send",
            "params": {
                "id": effective_id,
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": message_text}],
                },
            },
        }

    @staticmethod
    def _extract_response_text(data: dict) -> str:
        if "error" in data and data["error"] is not None:
            err = data["error"]
            err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            return f"[A2A Refusal] {err_msg}"

        result = data.get("result")
        if not result or not isinstance(result, dict):
            return str(result) if result is not None else ""

        # Check message parts
        msg = result.get("message")
        if isinstance(msg, dict):
            parts = msg.get("parts")
            if isinstance(parts, list):
                texts = [
                    str(part.get("text", ""))
                    for part in parts
                    if isinstance(part, dict) and "text" in part
                ]
                if texts:
                    return "\n".join(texts)

        # Check artifacts
        artifacts = result.get("artifacts")
        if isinstance(artifacts, list):
            texts = []
            for art in artifacts:
                if isinstance(art, dict):
                    parts = art.get("parts")
                    if isinstance(parts, list):
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                texts.append(str(part.get("text", "")))
            if texts:
                return "\n".join(texts)

        # Check status message
        status = result.get("status")
        if isinstance(status, dict) and "message" in status:
            return str(status["message"])

        return str(result)

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Union[Message, None]]:
        if not self.uri:
            raise BadGeneratorException("A2AGenerator requires a valid URI endpoint.")

        if isinstance(prompt, Conversation):
            prompt_text = prompt.last_message().text
        elif isinstance(prompt, str):
            prompt_text = prompt
        else:
            prompt_text = str(prompt)

        current_dialect = "v02" if self.dialect == "v02" else "v03"
        payload = self._build_payload(current_dialect, prompt_text)
        headers = self._build_headers()

        try:
            resp = requests.post(
                self.uri,
                json=payload,
                headers=headers,
                timeout=self.request_timeout,
                verify=self.verify_ssl,
            )
            resp.raise_for_status()
            data = resp.json()

            # Handle automatic fallback from 0.3 to 0.2 if method not found
            if (
                self.dialect == "auto"
                and current_dialect == "v03"
                and isinstance(data, dict)
                and data.get("error", {}).get("code") == RPC_METHOD_NOT_FOUND
            ):
                logger.info(
                    "A2A method message/send returned -32601; falling back to tasks/send (0.2)"
                )
                current_dialect = "v02"
                payload = self._build_payload(current_dialect, prompt_text)
                retry_resp = requests.post(
                    self.uri,
                    json=payload,
                    headers=headers,
                    timeout=self.request_timeout,
                    verify=self.verify_ssl,
                )
                retry_resp.raise_for_status()
                data = retry_resp.json()
                self.dialect = "v02"
            elif self.dialect == "auto":
                self.dialect = current_dialect

        except requests.RequestException as exc:
            logger.error("Failed to query A2A agent at %s: %s", self.uri, exc)
            raise ConnectionError(f"A2A communication failure: {exc}") from exc

        extracted_text = self._extract_response_text(data)

        # Update active task id
        if isinstance(data, dict) and "result" in data:
            res = data.get("result")
            if isinstance(res, dict):
                tid = res.get("taskId") or res.get("task_id") or res.get("id")
                if tid:
                    self.task_id = tid

        return [Message(text=extracted_text)]

    def get_agent_card(self) -> dict:
        """Fetch the Agent Card manifest from standard discovery paths."""
        paths = ["/.well-known/agent-card.json", "/agent.json"]
        headers = self._build_headers()
        base_url = self.uri.split("/tasks")[0].split("/message")[0]

        for p in paths:
            target_url = urljoin(base_url, p)
            try:
                resp = requests.get(
                    target_url,
                    headers=headers,
                    timeout=self.request_timeout,
                    verify=self.verify_ssl,
                )
                if resp.status_code == 200:
                    return resp.json()
            except requests.RequestException as exc:
                logger.debug("Failed to fetch agent card from %s: %s", target_url, exc)
        return {}


DEFAULT_CLASS = "A2AGenerator"

