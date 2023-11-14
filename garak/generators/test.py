#!/usr/bin/env python3
"""Test generators

These give simple system responses, intended for testing.
"""

from typing import List

from garak.generators.base import Generator


class Blank(Generator):
    supports_multiple_generations = True
    generator_family_name = "Test"
    name = "Blank"

    def _call_model(self, prompt: str) -> List[str]:
        return [""] * self.generations


class Repeat(Generator):
    supports_multiple_generations = True
    generator_family_name = "Test"
    name = "Repeat"

    def _call_model(self, prompt: str) -> List[str]:
        return [prompt] * self.generations


default_class = "Blank"
