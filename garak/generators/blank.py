#!/usr/bin/env python3

import logging

from colorama import Fore, Style

from garak.generators.base import Generator


class BlankGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name = name
        self.generations = generations
        print(
            f"🦜 loading {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: BlankGenerator"
        )
        logging.info("generator init: {self}")

    def generate(self, prompts):
        return [""] * self.generations


default_class = "BlankGenerator"
