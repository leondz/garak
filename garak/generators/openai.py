#!/usr/bin/env python3

import importlib
import os

from garak.generators.base import Generator

"""
sources:
* https://platform.openai.com/docs/models/model-endpoint-compatibility
* https://platform.openai.com/docs/model-index-for-researchers
"""
completion_models = (
    "text-davinci-003",
    "text-davinci-002",
    "text-curie-001",
    "text-babbage-001",
    "text-ada-001",
    "code-davinci-002",
    "code-davinci-001",
    "davinci-instruct-beta",
)
chat_models = (
    "gpt-4",
    "gpt-4-0314",
    "gpt-4-32k",
    "gpt-4-32k-0314",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0301",
)


class OpenAIGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"OpenAI {self.name}"
        self.generations = generations

        self.temperature = 0.7
        self.max_tokens = 150
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.stop = ["#", ";"]

        self.generator_family_name = "OpenAI"
        super().__init__(name)

        self.openai = importlib.import_module("openai")
        self.openai.api_key = os.getenv("OPENAI_API_KEY", default=None)
        if self.openai.api_key == None:
            raise Exception(
                'Put the OpenAI API key in the OPENAI_API_KEY environment variable (this was empty)\n \
                e.g.: export OPENAI_API_KEY="sk-123XXXXXXXXXXXX"'
            )

        if self.name in completion_models:
            self.generator = self.openai.Completion
        elif self.name in chat_models:
            self.generator = self.openai.ChatCompletion
        elif self.name == "":
            openai_model_list = sorted(
                [m["id"] for m in self.openai.Model().list()["data"]]
            )
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

    def generate(self, prompt):
        if self.generator == self.openai.Completion:
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
            return [c["text"] for c in response["choices"]]
        elif self.generator == self.openai.ChatCompletion:
            response = self.generator.create(
                model=self.name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                top_p=self.top_p,
                n=self.generations,
                stop=self.stop,
                max_tokens=self.max_tokens,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
            )
            return [c["message"]["content"] for c in response["choices"]]
        else:
            raise ValueError(
                f"Unsupported model at generation time in generators/openai.py - please add a clause!"
            )


default_class = "OpenAIGenerator"
