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


import logging
import os
import re
import subprocess

from garak import _config
from garak.generators.base import Generator


class GgmlGenerator(Generator):
    """Generator interface for ggml models.

    Set the path to the model as the model name, and put the path to the ggml executable in environment variable GGML_MAIN_PATH.
    """

    repeat_penalty = 1.1
    presence_penalty = 0.0
    frequency_penalty = 0.0
    top_k = 40
    top_p = 0.95
    temperature = 0.8
    exception_on_failure = True
    first_call = True

    generator_family_name = "ggml"

    def command_params(self):
        return {
            "-m": self.name,
            "-n": self.max_tokens,
            "--repeat-penalty": self.repeat_penalty,
            "--presence-penalty": self.presence_penalty,
            "--frequency-penalty": self.frequency_penalty,
            "--top-k": self.top_k,
            "--top-p": self.top_p,
            "--temp": self.temperature,
            "-s": self.seed, # this value cannot be `None` it requires an integer value 0 could be consistent not provided will be a constant and `-1` would produce random seeds
        }


    def __init__(self, name, generations=10):
        self.path_to_ggml_main = os.getenv("GGML_MAIN_PATH")
        if not os.path.isfile(self.path_to_ggml_main):
            raise RuntimeError("Unable to locate executable")

        # check for valid executable here
        # when llama.cpp version < 1046 format supported is `.ggml` also provided as `.bin`
        # version >= 1046 file format it `.guff`

        self.seed = _config.run.seed
        super().__init__(name, generations=generations)
        # consider validating name here as it is really a filename
        # the extension could be validated and warn if does not match a supported
        # type, also the file should be validated to exist in for that time being

    def _call_model(self, prompt):
        command = [
            self.path_to_ggml_main,
            "-p",
            prompt,
        ]
        # test are required params for None type
        for key, value in self.command_params().items():
            if value is not None:
                command.append(key)
                command.append(value)
        command = [str(param) for param in command]
        if _config.system.verbose > 1:
            print("GGML invoked with", command)
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=self.exception_on_failure,
            )
            output = result.stdout.decode("utf-8")
            output = re.sub("^" + re.escape(prompt.lstrip()), "", output.lstrip())
            self.first_call = False
            return output
        except subprocess.CalledProcessError as err:
            # if this is the first call attempt, raise the exception to indicate
            # the generator is mis-configured
            print(err.stderr.decode("utf-8"))
            logging.error(err.stderr.decode("utf-8"))
            if self.first_call:
                raise err
            return None
        except Exception as err:
            logging.error(err)
            return None


default_class = "GgmlGenerator"
