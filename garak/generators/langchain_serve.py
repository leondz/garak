import logging
import json
import requests

from garak import _config
from garak.generators.base import Generator

class LangChainServeLLMGenerator(Generator):
    """Class supporting LangChain Serve LLM interfaces via HTTP POST requests.

    This class facilitates communication with LangChain Serve's LLMs through a web API, making it possible
    to utilize external LLMs not directly integrated into the LangChain library. It requires setting up
    an API endpoint using langchain serve.

    Utilizes the HTTP POST method to send prompts to the specified LLM and retrieves the generated text
    response. It is necessary to ensure that the API endpoint is correctly set up and accessible.

    Inherits from Garak's base Generator class, extending its capabilities to support web-based LLM services.

    Set endpoint name with --model_name. Example: --model_name=http://127.0.0.1:8000/rag-chroma-private and it's "invoke" endpoint will be used.

    To use, set the appropriate API endpoint and configuration hash (if needed) before invoking the LLM with a prompt.
    """

    generator_family_name = "LangChainServe"
    config_hash = "default"

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"LangChain Serve LLM {self.name}"
        self.generations = generations
        self.api_endpoint = f"{_config.plugins.model_name}/invoke"

        super().__init__(name, generations=generations)

    def _call_model(self, prompt: str) -> str:
        """Makes an HTTP POST request to the LangChain Serve API endpoint to invoke the LLM with a given prompt."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        payload = {
            "input": prompt,
            "config": {},
            "kwargs": {} 
        }

        try:
            response = requests.post(f"{self.api_endpoint}?config_hash={self.config_hash}",
                                     headers=headers,
                                     data=json.dumps(payload))
            response.raise_for_status()
            if "output" not in response.json():
                logging.error("No output found in response: %s", response.json())
                raise ValueError("No output found in response")
            result = response.json().get("output")
            return result
        except requests.exceptions.RequestException as e:
            logging.error("HTTP Request failed: %s", e)
            return ""

default_class = "LangChainServeLLMGenerator"