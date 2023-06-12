#!/usr/bin/env python3

import os
import re
import subprocess

import garak._config
from garak.generators.base import Generator


class LLaMaGgmlGenerator(Generator):
    repeat_penalty = 1.1
    presence_penalty = 0.0
    frequency_penalty = 0.0
    top_k = 40
    top_p = 0.95
    temperature = 0.8

    generator_family_name = "ggml"

    def __init__(self, name, generations=10):
        self.path_to_ggml_main = os.getenv("GGML_MAIN_PATH")

        self.seed = garak._config.seed
        super().__init__(name, generations=generations)

    def _call_ggml(self, prompt):
        command = [
            self.path_to_ggml_main,
            "-m",
            self.name,
            "-n",
            self.max_tokens,
            "--repeat-penalty",
            self.repeat_penalty,
            "--presence-penalty",
            self.presence_penalty,
            "--frequency-penalty",
            self.frequency_penalty,
            "--top-k",
            self.top_k,
            "--top-p",
            self.top_p,
            "--temp",
            self.temperature,
            "-s",
            self.seed,
            "-p",
            prompt,
        ]
        command = [str(param) for param in command]
        if garak._config.args.verbose > 1:
            print("GGML invoked with", command)
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        output = result.stdout.decode("utf-8")
        output = re.sub("^" + re.escape(prompt.lstrip()), "", output.lstrip())
        return output

    def generate(self, prompt):
        outputs = []
        for g in range(self.generations):
            output = self._call_ggml(prompt)
            outputs.append(output)
        return outputs


default_class = "LLaMaGgmlGenerator"
