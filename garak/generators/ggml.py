#!/usr/bin/env python3

import os
import re
import subprocess

import garak._config
from garak.generators.base import Generator


class LLaMaGgmlGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name = name
        self.generations = generations

        self.path_to_ggml_man = os.getenv("GGML_MAIN_PATH")

        self.max_tokens = 128
        self.repeat_penalty = 1.1
        self.presence_penalty = 0.0
        self.frequency_penalty = 0.0
        self.top_k = 40
        self.top_p = 0.95
        self.temperature = 0.8
        self.seed = garak._config.seed

        self.generator_family_name = "ggml"
        super().__init__(name)

    def _call_ggml(self, prompt):
        command = [
            self.path_to_ggml_man,
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
