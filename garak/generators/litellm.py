"""LiteLLM model support

Support for LiteLLM, which allows calling LLM APIs using the OpenAI format.

Depending on the model name provider, LiteLLM automatically
reads API keys from the respective environment variables.
(e.g. OPENAI_API_KEY for OpenAI models)

API key can also be directly set in the supplied generator json config.
This also enables support for any custom provider that follows the OAI format.

e.g Supply a JSON like this for Ollama's OAI api:
```json
{
    "litellm": {
        "LiteLLMGenerator" : {
            "api_base" : "http://localhost:11434/v1",
            "provider" : "openai",
            "api_key" : "test"
        }
    }
}
```

The above is an example of a config to connect LiteLLM with Ollama's OpenAI compatible API.

Then, when invoking garak, we pass it the path to the generator option file.

```
python -m garak --model_type litellm --model_name "phi" --generator_option_file ollama_base.json -p dan
```
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
    "petals",
    "palm/",
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
    """Generator wrapper using LiteLLM to allow access to different providers using the OpenAI API format."""

    ENV_VAR = "OPENAI_API_KEY"
    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "stop": ["#", ";"],
    }

    supports_multiple_generations = True
    generator_family_name = "LiteLLM"

    _supported_params = (
        "name",
        "generations",
        "context_len",
        "max_tokens",
        "api_key",
        "provider",
        "api_base",
        "temperature",
        "top_p",
        "top_k",
        "frequency_penalty",
        "presence_penalty",
        "stop",
    )

    def __init__(self, name: str = "", generations: int = 10, config_root=_config):
        self.name = name
        self.api_base = None
        self.api_key = None
        self.provider = None
        self.key_env_var = self.ENV_VAR
        self.generations = generations
        self._load_config(config_root)
        self.fullname = f"LiteLLM {self.name}"
        self.supports_multiple_generations = not any(
            self.name.startswith(provider)
            for provider in unsupported_multiple_gen_providers
        )

        super().__init__(
            self.name, generations=self.generations, config_root=config_root
        )

        if self.provider is None:
            raise ValueError(
                "litellm generator needs to have a provider value configured - see docs"
            )
        elif (
            self.api_key is None
        ):  # TODO: special case where api_key is not always required
            if self.provider == "openai":
                self.api_key = getenv(self.key_env_var, None)
                if self.api_key is None:
                    raise APIKeyMissingError(
                        f"Please supply an OpenAI API key in the {self.key_env_var} environment variable"
                        " or in the configuration file"
                    )

    @backoff.on_exception(backoff.fibo, Exception, max_value=70)
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
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
            return []

        response = litellm.completion(
            model=self.name,
            messages=prompt,
            temperature=self.temperature,
            top_p=self.top_p,
            n=generations_this_call,
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
            return [response.choices[0].message.content]


DEFAULT_CLASS = "LiteLLMGenerator"
