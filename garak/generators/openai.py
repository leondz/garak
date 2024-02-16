#!/usr/bin/env python3
"""OpenAI API generator

Supports chat + chatcompletion models. Put your OpenAI API key in
an environment variable called OPENAI_API_KEY. Put the name of the
model you want in either the --model_name command line parameter, or
pass it as an argument to the OpenAIGenerator constructor.

sources:
* https://platform.openai.com/docs/models/model-endpoint-compatibility
* https://platform.openai.com/docs/model-index-for-researchers
"""

import os
import re
import logging
from typing import List, Union

import openai
import backoff

from garak.generators.base import Generator

completion_models = (
    "gpt-3.5-turbo-instruct",
    "text-davinci-003",
    "text-davinci-002",
    "text-curie-001",
    "text-babbage-001",
    "text-ada-001",
    "code-davinci-002",
    "code-davinci-001",
    "davinci-instruct-beta",
    "davinci",
    "curie",
    "babbage",
    "ada",
)
chat_models = (
    "gpt-4",
    "gpt-4-32k",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0301",
)


class OpenAIGenerator(Generator):
    """Generator wrapper for OpenAI text2text models. Expects API key in the OPENAI_API_KEY environment variable"""

    supports_multiple_generations = True
    generator_family_name = "OpenAI"

    temperature = 0.7
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = ["#", ";"]

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"OpenAI {self.name}"

        super().__init__(name, generations=generations)

        api_key = os.getenv("OPENAI_API_KEY", default=None)
        if api_key is None:
            raise ValueError(
                'Put the OpenAI API key in the OPENAI_API_KEY environment variable (this was empty)\n \
                e.g.: export OPENAI_API_KEY="sk-123XXXXXXXXXXXX"'
            )

        self.client = openai.OpenAI(api_key=api_key)

        if self.name in completion_models:
            self.generator = self.client.completions
        elif self.name in chat_models:
            self.generator = self.client.chat.completions
        elif "-".join(self.name.split("-")[:-1]) in chat_models and re.match(
            r"^.+-[01][0-9][0-3][0-9]$", self.name
        ):  # handle model names -MMDDish suffix
            self.generator = self.client.completions

        elif self.name == "":
            openai_model_list = sorted([m.id for m in self.client.models.list().data])
            raise ValueError(
                "Model name is required for OpenAI, use --model_name\n"
                + "  API returns following available models: ▶️   "
                + "  ".join(openai_model_list)
                + "\n"
                + "  ⚠️  Not all these are text generation models"
            )
        else:
            raise ValueError(
                f"No OpenAI API defined for '{self.name}' in generators/openai.py - please add one!"
            )

    # noinspection PyArgumentList
    @backoff.on_exception(
        backoff.fibo,
        (
            openai.RateLimitError,
            openai.InternalServerError,
            openai.APIError,
            openai.APITimeoutError,
            openai.APIConnectionError,
        ),
        max_value=70,
    )
    def _call_model(self, prompt: Union[str, list[dict]]) -> List[str]:
        if self.generator == self.client.completions:
            if not isinstance(prompt, str):
                msg = (
                    f"Expected a string for OpenAI completions model {self.name}, but got {type(prompt)}. "
                    f"Returning nothing!"
                )
                logging.error(msg)
                print(msg)
                return list()

            response = self.generator.create(
                model=self.name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                n=self.generations,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=self.stop,
            )
            return [c.text for c in response.choices]

        elif self.generator == self.client.chat.completions:
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            elif isinstance(prompt, list):
                messages = prompt
            else:
                msg = (
                    f"Expected a list of dicts for OpenAI Chat model {self.name}, but got {type(prompt)} instead. "
                    f"Returning nothing!"
                )
                logging.error(msg)
                print(msg)
                return list()
            response = self.generator.create(
                model=self.name,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
                n=self.generations,
                stop=self.stop,
                max_tokens=self.max_tokens,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
            )
            return [c.message.content for c in response.choices]

        else:
            raise ValueError(
                "Unsupported model at generation time in generators/openai.py - please add a clause!"
            )


default_class = "OpenAIGenerator"
