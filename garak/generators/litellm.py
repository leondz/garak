"""LiteLLM model support

Support for LiteLLM, which allows calling LLM APIs using the OpenAI format.
"""

import logging

from os import getenv
from typing import List, Union

import backoff

import litellm

from garak import _config
from garak.generators.base import Generator

# Fix issue with Ollama which does not support `presence_penalty`
litellm.drop_params = True
# Suppress log messages from LiteLLM
litellm.verbose_logger.disabled = True
# litellm.set_verbose = True

# Based on the param support matrix below:
# https://docs.litellm.ai/docs/completion/input
# Some providers do not support the `n` parameter
# and thus cannot generate multiple completions in one request
unsupported_multiple_gen_providers = (
    "openrouter/",
    "claude",
    "replicate/",
    "bedrock",
    "petals," "palm/",
    "together_ai/",
    "text-bison",
    "text-bison@001",
    "chat-bison",
    "chat-bison@001",
    "chat-bison-32k",
    "code-bison",
    "code-bison@001",
    "code-gecko@001",
    "code-gecko@latest",
    "codechat-bison",
    "codechat-bison@001",
    "codechat-bison-32k",
)


class LiteLLMGenerator(Generator):
    supports_multiple_generations = True
    generator_family_name = "LiteLLM"

    temperature = 0.7
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = ["#", ";"]

    def __init__(self, name: str, generations: int = 10):
        self.name = name
        self.fullname = f"LiteLLM {self.name}"
        self.generations = generations
        self.api_base = None
        self.api_key = None
        self.provider = None
        self.supports_multiple_generations = not any(
            self.name.startswith(provider)
            for provider in unsupported_multiple_gen_providers
        )

        super().__init__(name, generations=generations)

        if "litellm.LiteLLMGenerator" in _config.plugins.generators:
            for field in (
                "api_key",
                "provider",
                "api_base",
                "temperature",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
            ):
                if field in _config.plugins.generators["litellm.LiteLLMGenerator"]:
                    setattr(
                        self,
                        field,
                        _config.plugins.generators["litellm.LiteLLMGenerator"][field],
                    )

                    if field == "provider" and self.api_key is None:
                        if self.provider == "openai":
                            self.api_key = getenv("OPENAI_API_KEY", None)
                            if self.api_key is None:
                                raise ValueError(
                                    "Please supply an OpenAI API key in the OPENAI_API_KEY environment variable"
                                    " or in the configuration file"
                                )

    @backoff.on_exception(backoff.fibo, Exception, max_value=70)
    def _call_model(self, prompt: Union[str, List[dict]]) -> List[str] | str | None:
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            prompt = prompt
        else:
            msg = (
                f"Expected a list of dicts for LiteLLM model {self.name}, but got {type(prompt)} instead. "
                f"Returning nothing!"
            )
            logging.error(msg)
            print(msg)
            return list()

        response = litellm.completion(
            model=self.name,
            messages=prompt,
            temperature=self.temperature,
            top_p=self.top_p,
            n=self.generations,
            stop=self.stop,
            max_tokens=self.max_tokens,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            api_base=self.api_base,
            custom_llm_provider=self.provider,
            api_key=self.api_key,
        )

        if self.supports_multiple_generations:
            return [c.message.content for c in response.choices]
        else:
            return response.choices[0].message.content


default_class = "LiteLLMGenerator"
