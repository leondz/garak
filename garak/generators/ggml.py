#!/usr/bin/env python3
"""ggml generator support

This generator works with ggml models like llama.cpp.

Put the path to your ggml executable (e.g. "/home/leon/llama.cpp/main") in
an environment variable named GGML_MAIN_PATH, and pass the path to the
model you want to run either using --model_name on the command line
or as the constructor parameter when instantiating LLaMaGgmlGenerator.

Compatibility or other problems? Please let us know!
 https://github.com/leondz/garak/issues
"""


import os
import re
import subprocess

import garak._config
from garak.generators.base import Generator


class GgmlGenerator(Generator):
    repeat_penalty = 1.1
    presence_penalty = 0.0
    frequency_penalty = 0.0
    top_k = 40
    top_p = 0.95
    temperature = 0.8
    exception_on_failure = True

    generator_family_name = "ggml"

    def __init__(self, name, generations=10):
        self.path_to_ggml_main = os.getenv("GGML_MAIN_PATH")

        self.seed = garak._config.seed
        super().__init__(name, generations=generations)

    def _call_model(self, prompt):
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
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=self.exception_on_failure,
        )
        output = result.stdout.decode("utf-8")
        output = re.sub("^" + re.escape(prompt.lstrip()), "", output.lstrip())
        return output


default_class = "GgmlGenerator"
