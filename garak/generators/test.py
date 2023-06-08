#!/usr/bin/env python3

from garak.generators.base import Generator


class Blank(Generator):
    def __init__(self, name="", generations=10):
        self.generator_family_name = "Blank"
        super().__init__(name=name, generations=generations)

    def generate(self, prompts):
        return [""] * self.generations


class Repeat(Generator):
    def __init__(self, name="", generations=10):
        self.generator_family_name = "Repeat"
        super().__init__(name=name, generations=generations)

    def generate(self, prompt):
        return [prompt] * self.generations


default_class = "Blank"
