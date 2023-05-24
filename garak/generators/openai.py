#!/usr/bin/env python3

import logging
import os

from colorama import Fore, Style
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

from garak.generators.base import Generator


class OpenAIGenerator(Generator):
    def __init__(self, name, model_type="completion", generations=10):
        self.name = name
        self.fullname = f"OpenAI {self.name}"
        self.generations = generations
        self.model_type = model_type

        self.temperature = 0.7
        self.max_tokens = 150
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.stop = ["#", ";"]
        print(
            f"loading {Style.RESET_ALL}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: OpenAI:{name}"
        )
        logging.info("generator init: {self}")

        if model_type == "completion":
            self.generator = openai.Completion
        elif model_type == "chat":
            self.generator = openai.Completion
        else:
            raise ValueError(
                f"No support yet for requested {model_type} OpenAI model type"
            )

    def generate(self, prompt):
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


default_class = "OpenAIGenerator"
