# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""LangChain generator support
"""


import logging
import tqdm

import langchain.llms

from garak.generators.base import Generator


class LangChainLLMGenerator(Generator):
    """Class supporting LangChain LLM interfaces

    See LangChain's supported models here,
      https://python.langchain.com/docs/integrations/llms/

    Calls invoke with the prompt and relays the response. No per-LLM specific
    checking, so make sure the right environment variables are set.

    Set --model_name to the LLM type required.

    Explicitly, garak delegates the majority of responsibility here:

    * the generator calls invoke() on the LLM, which seems to be the most
      widely supported method
    * langchain-relevant environment vars need to be set up there
    * There's no support for chains, just the langchain LLM interface.
    """

    temperature = 0.750
    k = 0
    p = 0.75
    preset = None
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = []
    generator_family_name = "LangChain"

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"LangChain LLM {self.name}"
        self.generations = generations

        super().__init__(name, generations=generations)

        try:
            llm = getattr(langchain.llms, self.name)()
        except Exception as e:
            logging.error("Failed to import Langchain module: %s", repr(e))
            raise e

        self.generator = llm

    def _call_model(self, prompt: str, generations_this_call: int = 1) -> str:
        """
        Continuation generation method for LangChain LLM integrations.

        This calls invoke once per generation; invoke() seems to have the best
        support across LangChain LLM integrations.
        """
        return self.generator.invoke(prompt)


default_class = "LangChainLLMGenerator"
