"""LiteLLM model support

Support for LiteLLM, which allows calling LLM APIs using the OpenAI format.
"""

import logging

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
        self.provider = None

        super().__init__(name, generations=generations)

        if "litellm.LiteLLMGenerator" in _config.plugins.generators:
            for field in (
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
        )

        return [c.message.content for c in response.choices]


default_class = "LiteLLMGenerator"
