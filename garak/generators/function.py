#!/usr/bin/env python3

import importlib
from typing import List

import garak._config
from garak.generators.base import Generator


class Single(Generator):
    description = "pass a module#function to be called as generator, with format function(prompt:str, **kwargs)->str"
    uri = "https://github.com/leondz/garak/issues/137"

    generator_family_name = "function"

    def __init__(self, name="", **kwargs):  # name="", generations=self.generations):
        gen_module_name, gen_function_name = name.split("#")
        if "generations" in kwargs:
            self.generations = kwargs["generations"]
            del kwargs["generations"]

        self.kwargs = kwargs

        gen_module = importlib.import_module(gen_module_name)
        self.generator = getattr(gen_module, gen_function_name)

        super().__init__(name, generations=self.generations)

    def generate(self, prompt) -> List[str]:
        outputs = []
        for i in range(self.generations):
            outputs.append(self.generator(prompt, **self.kwargs))
        return outputs


class Multiple(Single):
    description = "pass a module#function to be called as generator, with format function(prompt:str, generations:int, **kwargs)->List[str]"

    def generate(self, prompt) -> List[str]:
        outputs = self.generator(prompt, generations=self.generations, **self.kwargs)
        return outputs


default_class = "Single"
