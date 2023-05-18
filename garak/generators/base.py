#!/usr/bin/env python3

from colorama import Fore, Style

class Generator:
    def __init__(self, name, generations=10):
        self.name=name
        self.generations=generations
        print(f'loading empty {Style.RESET_ALL}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: {name}')

    def generate(self, prompts):
        outputs = [self.generator(i) for i in prompts]
        return outputs
