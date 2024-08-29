"""Ollama interface"""


from typing import List, Union

import backoff
import ollama

from garak import _config
from garak.generators.base import Generator

def _give_up(error):
    return isinstance(error, ollama.ResponseError) and error.status_code == 404

class OllamaGenerator(Generator):
    """Interface for Ollama endpoints    

        Model names can be passed in short form like "llama2" or specific versions or sizes like "gemma:7b" or "llama2:latest"
    """

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "timeout": 30, # Add a timeout of 30 seconds. Ollama can tend to hang forever on failures, if this is not present
        "host": "127.0.0.1:11434" # The default host of an Ollama server. This should maybe be loaded from a config file somewhere
    }

    active = True
    generator_family_name = "Ollama"

    def __init__(self, name="", generations=10, config_root=_config):        
        super().__init__(name, generations, config_root) # Sets the name and generations

        self.client = ollama.Client(self.DEFAULT_PARAMS['host'], timeout=self.DEFAULT_PARAMS["timeout"]) # Instantiates the client with the timeout

    @backoff.on_exception(backoff.fibo, (TimeoutError, ollama.ResponseError), max_value=70, giveup=_give_up)
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[Union[str, None]]:
        response = self.client.generate(self.name, prompt)
        return [response['response']]

class OllamaGeneratorChat(OllamaGenerator):
    """Interface for Ollama endpoints, using the chat functionality 

        Model names can be passed in short form like "llama2" or specific versions or sizes like "gemma:7b" or "llama2:latest"
    """

    @backoff.on_exception(backoff.fibo, (TimeoutError, ollama.ResponseError), max_value=70, giveup=_give_up)
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[Union[str, None]]:
        response = self.client.chat(model=self.name, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return [response['message']['content']]
    
DEFAULT_CLASS = "OllamaGeneratorChat"