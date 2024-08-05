"""Azure OpenAI generator

Supports chat + chatcompletion models. Put your API key in the AZURE_API_KEY environment variable, 
the azure openai endpoint in the AZURE_ENDPOINT environment variable and the azure openai deployment name 
in AZURE_DEPLOYMENT_NAME environment variable.

Put the model name in either the --model_name command line parameter, or
pass it as an argument to the Generator constructor.
"""

import random
import os
from typing import List, Union

import openai

from garak import _config
from garak.generators.openai import OpenAICompatible, chat_models, completion_models, context_lengths

# lists derived from https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models
# some azure openai model names should be mapped to openai names
chat_models_openai = {
    "gpt-4": "gpt-4-turbo-2024-04-09", 
    "gpt-4o": "gpt-4o", # links to latest version
    "gpt-4o-mini": "gpt-4o-mini", # links to latest version
    "gpt-35-turbo": "gpt-3.5-turbo-0125", 
    "gpt-35-turbo-16k": "gpt-3.5-turbo-16k", 
    "gpt-4-32k": "gpt-4-32k", 
}

completion_models_openai = {
    "gpt-35-turbo-instruct": "gpt-3.5-turbo-instruct", 
    "davinci-002": "davinci-002", 
    "babbage-002": "babbage-002", 
}

class AzureOpenAIChat(OpenAICompatible):
    """Wrapper for Azure Open AI. Expects AZURE_API_KEY, AZURE_ENDPOINT and AZURE_DEPLOYMENT_NAME environment variables.

    Uses the [OpenAI-compatible API](https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation)
    via direct HTTP request.

    To get started with this generator:
    #. Visit [https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models) and find the LLM you'd like to use.
    #. [Deploy a model](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model) and copy paste the model and deployment names
    #. On the Azure portal page for the Azure OpenAI you want to use click on "Resource Management -> Keys and Endpoint" and copy paste the API Key and endpoint. 
    #. In your console, Set the ``AZURE_API_KEY``, ``AZURE_ENDPOINT`` and ``AZURE_DEPLOYMENT_NAME`` variables.
    #. Run garak, setting ``--model_type`` to ``azure`` and ``--model_name`` to [the name of the model](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
    - e.g. ``gpt-4o``.
    """

    ENV_VAR = "AZURE_API_KEY"
    active = True
    generator_family_name = "Azure"
    name_backup = ""

    def __init__(self, name="", config_root=_config):
        if name in chat_models_openai:
            self.name = chat_models_openai[name]
        elif name in completion_models_openai:
            self.name = completion_models_openai[name]
        else:
            self.name = name

        self._load_config(config_root)
        if self.name in context_lengths:
            self.context_len = context_lengths[self.name]

        super().__init__(
            self.name, generations=self.generations, config_root=config_root
        )

    def _load_client(self):
        azure_endpoint = os.getenv("AZURE_ENDPOINT", default=None)
        if azure_endpoint is None:
            raise ValueError(
                'The AZURE_ENDPOINT environment variable is required.\n'
            )

        azure_deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", default=None)
        if azure_deployment_name is None:
            raise ValueError(
                'The AZURE_DEPLOYMENT_NAME environment variable is required.\n'
            )

        self.client = openai.AzureOpenAI(azure_endpoint=azure_endpoint, api_key=self.api_key)

        if self.name == "":
            openai_model_list = sorted([m.id for m in self.client.models.list().data])
            raise ValueError(
                f"Model name is required for {self.generator_family_name}, use --model_name\n"
                + "  API returns following available models: ▶️   "
                + "  ".join(openai_model_list)
                + "\n"
                + "  ⚠️  Not all these are text generation models"
            )

        if self.name in completion_models:
            self.generator = self.client.completions
        elif self.name in chat_models:
            self.generator = self.client.chat.completions
        elif "-".join(self.name.split("-")[:-1]) in chat_models and re.match(
            r"^.+-[01][0-9][0-3][0-9]$", self.name
        ):  # handle model names -MMDDish suffix
            self.generator = self.client.completions
        else:
            raise ValueError(
                f"No {self.generator_family_name} API defined for '{self.name}' in generators/openai.py - please add one!"
            )

        self.name_backup = self.name
        self.name = azure_deployment_name

    def _clear_client(self):
        self.generator = None
        self.client = None
        self.name = self.name_backup


class AzureOpenAICompletion(AzureOpenAIChat):
    """Wrapper for Azure Open AI. Expects AZURE_API_KEY, AZURE_ENDPOINT and AZURE_DEPLOYMENT_NAME environment variables.

    Uses the [OpenAI-compatible API](https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation)
    via direct HTTP request.

    To get started with this generator:
    #. Visit [https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models) and find the LLM you'd like to use.
    #. [Deploy a model](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model) and copy paste the model and deployment names
    #. On the Azure portal page for the Azure OpenAI you want to use click on "Resource Management -> Keys and Endpoint" and copy paste the API Key and endpoint. 
    #. In your console, Set the ``AZURE_API_KEY``, ``AZURE_ENDPOINT`` and ``AZURE_DEPLOYMENT_NAME`` variables.
    #. Run garak, setting ``--model_type`` to ``azure`` and ``--model_name`` to [the name of the model](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
    - e.g. ``gpt-4o``.
    """

    def _load_client(self):
        super()._load_client()
        self.generator = self.client.completions


DEFAULT_CLASS = "AzureOpenAIChat"
