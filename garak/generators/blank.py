#!/usr/bin/env python3

from garak.generators.base import Generator


class BlankGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name = ""
        self.generator_family_name = "Blank"
        super().__init__(name)

    def generate(self, prompts):
        return [""] * self.generations


default_class = "BlankGenerator"
