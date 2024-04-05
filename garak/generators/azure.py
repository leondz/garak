#!/usr/bin/env python3
"""Azure OpenAI API generator

Supports chat + chatcompletion models. Put your Azure OpenAI API key in
an environment variable called AZUREAI_API_KEY. Put your Azure OpenAI endpoint
in an environment variable called AZURE_ENDPOINT. Put the name of the model 
you want in either the --model_name command line parameter, or pass it as an
argument to the AzureAIGenerator constructor.

sources:
https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models
"""

import os
import re
import logging
from typing import List, Union

import openai
import backoff

from garak.generators.base import Generator

# lists derived from https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models
chat_models = (
    "gpt-4",  # links to latest version
    "gpt-35-turbo",  # links to latest version
    "gpt-4-32k",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview",
    "gpt-4-0613",
    "gpt-4-0314",
    "gpt-4-32k-0613",
    "gpt-4-32k-0314",
    "gpt-35-turbo-0125",
    "gpt-35-turbo-1106",
    "gpt-35-turbo-16k",
    "gpt-35-turbo-0613",  # deprecated, shutdown 2024-06-13
    "gpt-35-turbo-16k-0613",  # # deprecated, shutdown 2024-06-13  
)

completion_models = (
    "gpt-35-turbo-instruct",
    "davinci-002",
    "babbage-002",
     "dall-e-3"
)


class AzureAIGenerator(Generator):
    """Generator wrapper for Azure OpenAI text2text models. Expects API key in the AZUREAI_API_KEY environment variable"""

    supports_multiple_generations = True
    generator_family_name = "AzureAI"

    temperature = 0.7
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = ["#", ";"]

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"Azure OpenAI {self.name}"

        super().__init__(name, generations=generations)

        api_key = os.getenv("AZUREAI_API_KEY", default=None)
        if api_key is None:
            raise ValueError(
                'Put the Azure OpenAI API key in the AZUREAI_API_KEY environment variable (this was empty)\n \
                e.g.: export AZUREAI_API_KEY="sk-123Xgenerators/azure.pyXXXXXXXXXXX"'
            )

        azure_endpoint = os.getenv("AZURE_ENDPOINT", default=None)
        if azure_endpoint is None:
            raise ValueError(
                'Put the Azure endpoint URL in the AZURE_ENDPOPINT environment variable (this was empty)\n \
                e.g.: export AZURE_ENDPOPINT=https://ai-proxy.<company>.com'
            )

        self.client = openai.AzureOpenAI(
                        api_version="2023-12-01-preview",
                        azure_endpoint=azure_endpoint,
                        api_key=api_key
                        )

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
                "Model name is required for Azure OpenAI, use --model_name\n"
                + "  API returns following available models: ▶️   "
                + "  ".join(openai_model_list)
                + "\n"
                + "  ⚠️  Not all these are text generation models"
            )
        else:
            raise ValueError(
                f"No Azure OpenAI API defined for '{self.name}' in generators/azure.py - please add one!"
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
                    f"Expected a string for Azure OpenAI completions model {self.name}, but got {type(prompt)}. "
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
                    f"Expected a list of dicts for Azure OpenAI Chat model {self.name}, but got {type(prompt)} instead. "
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
                "Unsupported model at generation time in generators/azure.py - please add a clause!"
            )


default_class = "AzureAIGenerator"
