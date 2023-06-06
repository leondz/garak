#!/usr/bin/env python3

import copy
import json
import logging
from typing import List

from colorama import Fore, Style
from tqdm import tqdm

from garak.attempt import *
from garak._config import reportfile, args


class Probe:
    """Base class for objects that define and execute LLM evaluations"""

    def __init__(self):
        if "name" not in dir(self):
            self.name = None
        if "description" not in dir(self):
            self.description = "Empty probe"
        if "uri" not in dir(self):
            self.uri = ""
        if "bcp47" not in dir(self):
            self.bcp47 = None  # language this is for, in bcp47 format; * for all langs
        if "recommended_detector" not in dir(self):
            self.recommended_detector = ["toxicity.ToxicCommentModelDetector"]
        if "probename" not in dir(self):
            self.probename = str(self.__class__).split("'")[1]
        if not args or args.verbose > 0:
            print(
                f"loading {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probe: {Style.RESET_ALL}{self.probename}"
            )
        logging.info(f"probe init: {self}")

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        return attempt

    def probe(self, generator) -> List[Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug(f"probe execute: {self}")

        attempts = []
        prompts = list(self.prompts)
        prompt_iterator = tqdm(prompts, leave=False)
        prompt_iterator.set_description(self.probename.replace("garak.", ""))

        for seq, prompt in enumerate(prompt_iterator):
            this_attempt = Attempt()
            this_attempt.prompt = prompt
            this_attempt.probe_classname = self.__class__.__name__
            this_attempt.status = ATTEMPT_STARTED
            this_attempt.outputs = generator.generate(prompt)
            this_attempt = self._attempt_prestore_hook(this_attempt, seq)
            reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            attempts.append(copy.deepcopy(this_attempt))
        return attempts


class TextProbe(Probe):
    """Subclass of Probe for text-based probes using a list of prompts, kept in `self.prompts`."""

    def __init__(self):
        super().__init__()
        self.prompts = []

    def probe(self, generator) -> List[Attempt]:
        return super().probe(generator)
