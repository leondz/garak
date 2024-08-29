"""OctoML LLM interface"""


from typing import List, Union

import backoff
import ollama

from garak import _config
from garak.generators.base import Generator

class OllamaGenerator(Generator):
    """Interface for Ollama endpoints    

        Model names can be passed in short form like "llama2" or specific versions or sizes like "gemma:7b" or "llama2:latest"
    """

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "timeout": 30 # Add a timeout of 30 seconds. Ollama can tend to hang forever, if this is not present
    }

    active = True
    generator_family_name = "Ollama"

    def __init__(self, name="", generations=10, config_root=_config):        
        super().__init__(name, generations, config_root) # Sets the name and generations

        self.client = ollama.Client(timeout=self.DEFAULT_PARAMS["timeout"]) # Instantiates the client with the timeout

    @backoff.on_exception(backoff.fibo, (TimeoutError, ollama.ResponseError), max_value=70)
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[Union[str, None]]:
        response = self.client.generate(self.name, prompt)
        return [response['response']]
