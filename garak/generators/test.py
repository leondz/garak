#!/usr/bin/env python3

from garak.generators.base import Generator


class Blank(Generator):
    generator_family_name = "Blank"

    def generate(self, prompt):
        return [""] * self.generations


class Repeat(Generator):
    generator_family_name = "Repeat"

    def generate(self, prompt):
        return [prompt] * self.generations


default_class = "Blank"
