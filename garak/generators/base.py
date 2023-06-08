#!/usr/bin/env python3

import logging
from typing import List

from colorama import Fore, Style


class Generator:
    def __init__(self, name="", generations=10):
        if "name" not in dir(self):
            self.name = name
        self.generations = generations
        if not self.generator_family_name:
            self.generator_family_name = "<empty>"
        print(
            f"🦜 loading {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}generator{Style.RESET_ALL}: {self.generator_family_name}: {self.name}"
        )
        logging.info(f"generator init: {self}")

    def _call_api(self, prompt: str) -> List[str]:
        return ""

    def generate(self, prompt) -> List[str]:
        outputs = []
        return outputs
