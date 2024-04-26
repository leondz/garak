"""Base Generator

All `garak` generators must inherit from this.
"""

import logging
from typing import List, Union

from colorama import Fore, Style
import tqdm

from garak import _config


class Generator:
    """Base class for objects that wrap an LLM or other text-to-text service"""

    name = "Generator"
    description = ""
    generations = 10
    max_tokens = 150
    temperature = None
    top_k = None
    active = True
    generator_family_name = None
    context_len = None

    supports_multiple_generations = (
        False  # can more than one generation be extracted per request?
    )

    def __init__(self, name="", generations=10):
        if "description" not in dir(self):
            self.description = self.__doc__.split("\n")[0]
        if name:
            self.name = name
        self.generations = generations
        if "fullname" not in dir(self):
            if self.generator_family_name is not None:
                self.fullname = f"{self.generator_family_name}:{self.name}"
            else:
                self.fullname = self.name
        if not self.generator_family_name:
            self.generator_family_name = "<empty>"
        print(
            f"🦜 loading {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: {self.generator_family_name}: {self.name}"
        )
        logging.info("generator init: %s", self)

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> Union[List[str], str, None]:
        """Takes a prompt and returns an API output

        _call_api() is fully responsible for the request, and should either
        succeed or raise an exception. The @backoff decorator can be helpful
        here - see garak.generators.openai for an example usage.

        Can return None if no response was elicited"""
        raise NotImplementedError

    def _pre_generate_hook(self):
        pass

    def clear_history(self):
        pass

    def generate(self, prompt: str, generations_this_call: int = -1) -> List[str]:
        """Manages the process of getting generations out from a prompt

        This will involve iterating through prompts, getting the generations
        from the model via a _call_* function, and returning the output

        Avoid overriding this - try to override _call_model or _call_api
        """

        self._pre_generate_hook()

        assert (
            generations_this_call >= -1
        ), f"Unexpected value for generations_per_call: {generations_this_call}"

        if generations_this_call == -1:
            generations_this_call = self.generations

        elif generations_this_call == 0:
            logging.debug("generate() called with generations_this_call = 0")
            return []

        if self.supports_multiple_generations:
            return self._call_model(prompt, generations_this_call)

        elif generations_this_call <= 1:
            return [self._call_model(prompt, generations_this_call)]

        else:
            outputs = []
            if (
                hasattr(_config.system, "parallel_requests")
                and _config.system.parallel_requests
                and isinstance(_config.system.parallel_requests, int)
                and _config.system.parallel_requests > 1
            ):
                from multiprocessing import Pool

                bar = tqdm.tqdm(total=generations_this_call, leave=False)
                bar.set_description(self.fullname[:55])

                with Pool(_config.system.parallel_requests) as pool:
                    for result in pool.imap_unordered(
                        self._call_model, [prompt] * generations_this_call
                    ):
                        outputs.append(result)
                        bar.update(1)

            else:
                generation_iterator = tqdm.tqdm(
                    list(range(generations_this_call)), leave=False
                )
                generation_iterator.set_description(self.fullname[:55])
                for i in generation_iterator:
                    outputs.append(self._call_model(prompt, generations_this_call))

            cleaned_outputs = [
                o for o in outputs if o is not None
            ]  # "None" means no good response
            outputs = cleaned_outputs

            return outputs
