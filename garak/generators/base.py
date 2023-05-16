#!/usr/bin/env python3

class BaseGenerator:
    def __init__(self, name):
        self.name=name
        print('loading empty '+Style.RESET_ALL+Fore.LIGHTMAGENTA_EX+'generator'+Style.RESET_ALL+': ', name)

    def generator(self, prompt):
        return None

    def generate(self, prompts):
        generations = [self.generator(i) for i in prompts]
        return generations
