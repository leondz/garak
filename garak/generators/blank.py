#!/usr/bin/env python3

from colorama import Fore, Style

from generators.base import Generator

class BlankGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name=name
        self.generations=generations
        print(f'loading {Style.RESET_ALL}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: BlankGenerator')

    def generate(self, prompts):
        return [""] * self.generations