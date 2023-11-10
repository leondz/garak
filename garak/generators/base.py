#!/usr/bin/env python3
"""Base Generator

All `garak` generators must inherit from this.
"""

import logging
from typing import List, Union

from colorama import Fore, Style
import tqdm

import garak._config


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

    supports_multiple_generations = (
        False  # can more than one generation be extracted per request?
    )

    def __init__(self, name="", generations=10):
        if "description" not in dir(self):
            self.description = self.__doc__.split("\n")[0]
        if name:
            self.name = name
        if not self.fullname:
            self.fullname = name
        self.generations = generations
        if not self.generator_family_name:
            self.generator_family_name = "<empty>"
        print(
            f"🦜 loading {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: {self.generator_family_name}: {self.name}"
        )
        logging.info("generator init: %s", self)

    def _call_model(self, prompt: str) -> Union[List[str], str]:
        """Takes a prompt and returns an API output

        _call_api() is fully responsible for the request, and should either
        succeed or raise an exception. The @backoff decorator can be helpful
        here - see garak.generators.openai for an example usage."""
        raise NotImplementedError

    def _pre_generate_hook(self):
        pass

    def generate(self, prompt: str) -> List[str]:
        """Manages the process of getting generations out from a prompt

        This will involve iterating through prompts, getting the generations
        from the model via a _call_* function, and returning the output

        Avoid overriding this - try to override _call_model or _call_api
        """

        self._pre_generate_hook()

        if self.supports_multiple_generations:
            return self._call_model(prompt)

        elif self.generations <= 1:
            return [self._call_model(prompt)]

        else:
            outputs = []
            if (
                garak._config.args
                and garak._config.args.parallel_requests
                and isinstance(garak._config.args.parallel_requests, int)
                and garak._config.args.parallel_requests > 1
            ):
                from multiprocessing import Pool

                bar = tqdm.tqdm(total=self.generations, leave=False)
                bar.set_description(self.fullname[:55])
                with Pool(garak._config.args.parallel_requests) as pool:
                    for result in pool.imap_unordered(
                        self._call_model, [prompt] * self.generations
                    ):
                        outputs.append(result)
                        bar.update(1)

            else:
                generation_iterator = tqdm.tqdm(
                    list(range(self.generations)), leave=False
                )
                generation_iterator.set_description(self.fullname[:55])
                for i in generation_iterator:
                    outputs.append(self._call_model(prompt))

            return outputs
