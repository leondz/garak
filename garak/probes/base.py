#!/usr/bin/env python3

import copy
import json
import logging

from colorama import Fore, Style
from tqdm import tqdm

import garak
from garak.harness.base import Attempt
from garak._config import reportfile, args


class Probe:
    def __init__(self):
        self.name = None
        self.description = "Empty probe"
        self.uri = ""
        self.bcp47 = None  # language this is for, in bcp47 format; * for all langs
        self.recommended_detector = ["toxicity.ToxicCommentModelDetector"]
        self.probename = str(self.__class__).split("'")[1]
        if not args or args.verbose > 0:
            print(
                f"loading {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probe: {Style.RESET_ALL}{self.probename}"
            )
        logging.info(f"probe init: {self}")

    def probe(self, generator):
        # attempt to exploit the target, return list of results
        results = []
        logging.debug(f"probe execute: {self}")

        attempts = []
        prompts = list(self.prompts)
        prompt_iterator = tqdm(prompts, leave=False)
        prompt_iterator.set_description(self.probename.replace("garak.", ""))

        for prompt in prompts:
            this_attempt = Attempt()
            this_attempt.prompt = prompt
            this_attempt.probe_classname = self.__class__.__name__
            this_attempt.status = garak.ATTEMPT_STARTED
            this_attempt.outputs = generator.generate(prompt)
            reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            attempts.append(copy.deepcopy(this_attempt))
        return attempts


class TextProbe(Probe):
    def __init__(self):
        super().__init__()
        self.prompts = []

    def probe(self, generator):
        return super().probe(generator)
