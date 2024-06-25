# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NVIDIA Inference Microservice LLM interface"""

from typing import List, Union

import openai

from garak.generators.openai import OpenAICompatible


class NVOpenAIChat(OpenAICompatible):
    """Wrapper for NVIDIA-hosted NIMs. Expects NIM_API_KEY environment variable.

    Uses the [OpenAI-compatible API](https://docs.nvidia.com/ai-enterprise/nim-llm/latest/openai-api.html)
    via direct HTTP request.

    To get started with this generator:
    #. Visit [https://build.nvidia.com/explore/reasoning](build.nvidia.com/explore/reasoning)
    and find the LLM you'd like to use.
    #. On the page for the LLM you want to use (e.g. [mixtral-8x7b-instruct](https://build.nvidia.com/mistralai/mixtral-8x7b-instruct)),
    click "Get API key" key above the code snippet. You may need to create an
    account. Copy this key.
    #. In your console, Set the ``NIM_API_KEY`` variable to this API key. On
    Linux, this might look like ``export NIM_API_KEY="nvapi-xXxXxXx"``.
    #. Run garak, setting ``--model_name`` to ``nim`` and ``--model_type`` to
    the name of the model on [build.nvidia.com](https://build.nvidia.com/)
    - e.g. ``mistralai/mixtral-8x7b-instruct-v0.1``.

    """

    # per https://docs.nvidia.com/ai-enterprise/nim-llm/latest/openai-api.html
    # 2024.05.02, `n>1` is not supported
    ENV_VAR = "NIM_API_KEY"
    DEFAULT_PARAMS = OpenAICompatible.DEFAULT_PARAMS | {
        "temperature": 0.1,
        "top_p": 0.7,
        "top_k": 0,  # top_k is hard set to zero as of 24.04.30
        "uri": "https://integrate.api.nvidia.com/v1/",
        "suppressed_params": {"n", "frequency_penalty", "presence_penalty"},
    }
    active = True
    supports_multiple_generations = False
    generator_family_name = "NIM"

    timeout = 60

    def _load_client(self):
        self.client = openai.OpenAI(base_url=self.uri, api_key=self.api_key)
        if self.name in ("", None):
            raise ValueError(
                "NIMs require model name to be set, e.g. --model_name mistralai/mistral-8x7b-instruct-v0.1\nCurrent models:\n"
                + "\n - ".join(
                    sorted([entry.id for entry in self.client.models.list().data])
                )
            )
        self.generator = self.client.chat.completions

    def _clear_client(self):
        self.generator = None
        self.client = None

    def _call_model(
        self, prompt: str | List[dict], generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        assert (
            generations_this_call == 1
        ), "generations_per_call / n > 1 is not supported"
        return super()._call_model(prompt, generations_this_call)


class NVOpenAICompletion(NVOpenAIChat):
    """Wrapper for NVIDIA-hosted NIMs. Expects NIM_API_KEY environment variable.

    Uses the [OpenAI-compatible API](https://docs.nvidia.com/ai-enterprise/nim-llm/latest/openai-api.html)
    via direct HTTP request.

    This generator supports only ``completion`` and NOT ``chat``-format models.

    To get started with this generator:
    #. Visit [build.nvidia.com/explore/reasoning](build.nvidia.com/explore/reasoning)
    and find the LLM you'd like to use.
    #. On the page for the LLM you want to use (e.g. [mixtral-8x7b-instruct](https://build.nvidia.com/mistralai/mixtral-8x7b-instruct)),
    click "Get API key" key above the code snippet. You may need to create an
    account. Copy this key.
    #. In your console, Set the ``NIM_API_KEY`` variable to this API key. On
    Linux, this might look like ``export NIM_API_KEY="nvapi-xXxXxXx"``.
    #. Run garak, setting ``--model_name`` to ``nim`` and ``--model_type`` to
    the name of the model on [build.nvidia.com](https://build.nvidia.com/)
    - e.g. ``mistralai/mixtral-8x7b-instruct-v0.1``.

    """

    def _load_client(self):
        self.client = openai.OpenAI(base_url=self.uri, api_key=self.api_key)
        self.generator = self.client.completions


DEFAULT_CLASS = "NVOpenAIChat"
