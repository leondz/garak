#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Websocket connector

These give simple system responses, intended for testing.
"""

from garak.generators.base import Generator


class Raw(Generator):
    """Sends prompts to the socket and expects plain generation as response

    Set name to the websocket address, e.g. ws://localhost:8765"""

    supports_multiple_generations = False
    generator_family_name = "Websocket"

    def _call_model(self, prompt: str) -> str:
        with self.connect(self.name) as websocket:
            websocket.send(prompt)
            message = websocket.recv()

        return message

    def __init__(self, name="", generations=10):
        super().__init__(name, generations)
        import websockets.sync.client

        self.connect = websockets.sync.client.connect


default_class = "Blank"
