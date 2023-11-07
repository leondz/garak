#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Langchain support

Support for Langchain's LLMs, listed here:

  https://python.langchain.com/docs/integrations/llms/

Calls invoke with the prompt and relays the response. No per-LLM specific
checking, so make sure the right environment variables are set. 
Set --model_name to the LLM type required.
"""


import logging
import tqdm

import langchain.llms

from garak.generators.base import Generator


class LangchainGenerator(Generator):
    temperature = 0.750
    k = 0
    p = 0.75
    preset = None
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = []
    generator_family_name = "Langchain"

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"Langchain {self.name}"
        self.generations = generations

        super().__init__(name, generations=generations)

        try:
            llm = getattr(langchain.llms, self.name)()
        except Exception as e:
            logging.error("Failed to import Langchain module: %s", e)
            raise e

        self.generator = llm

    def generate(self, prompt):
        outputs = []
        generation_iterator = tqdm.tqdm(list(range(self.generations)), leave=False)
        generation_iterator.set_description(self.fullname[:55])
        for i in generation_iterator:
            outputs.append(self.generator.invoke(prompt))
        return outputs


default_class = "LangchainGenerator"
