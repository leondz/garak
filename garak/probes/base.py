#!/usr/bin/env python3

import copy
import json
import logging
from typing import List

from colorama import Fore, Style
from tqdm import tqdm

from garak import _config
import garak.attempt


class Probe:
    """Base class for objects that define and execute LLM evaluations"""

    name = None
    description = "Empty probe"
    uri = ""
    bcp47 = None  # language this is for, in bcp47 format; * for all langs
    recommended_detector = ["always.Fail"]  # send a signal if this isn't overridden
    active = True
    avid_v = None  # vulnerability ID from [AVID](https://avidml.org/database/), e.g. AVID-2022-V013

    def __init__(self):
        if "probename" not in dir(self):
            self.probename = str(self.__class__).split("'")[1]
        if not _config.args or _config.args.verbose > 0:
            print(
                f"loading {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probe: {Style.RESET_ALL}{self.probename}"
            )
        logging.info(f"probe init: {self}")

    def _attempt_prestore_hook(
        self, attempt: garak.attempt.Attempt, seq: int
    ) -> garak.attempt.Attempt:
        return attempt

    def _generator_precall_hook(self, generator, attempt=None):
        pass

    def probe(self, generator) -> List[garak.attempt.Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug(f"probe execute: {self}")

        attempts = []
        prompts = list(self.prompts)
        prompt_iterator = tqdm(prompts, leave=False)
        prompt_iterator.set_description(self.probename.replace("garak.", ""))

        for seq, prompt in enumerate(prompt_iterator):
            this_attempt = garak.attempt.Attempt()
            this_attempt.prompt = prompt
            this_attempt.probe_classname = (
                str(self.__class__.__module__).replace("garak.probes.", "")
                + "."
                + self.__class__.__name__
            )
            this_attempt.status = garak.attempt.ATTEMPT_STARTED
            this_attempt = self._attempt_prestore_hook(this_attempt, seq)
            self._generator_precall_hook(generator, this_attempt)
            this_attempt.outputs = generator.generate(prompt)
            _config.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            attempts.append(copy.deepcopy(this_attempt))
        return attempts


class TextProbe(Probe):
    """Subclass of Probe for text-based probes using a list of prompts, kept in `self.prompts`."""

    prompts = []

    def __init__(self):
        super().__init__()

    def probe(self, generator) -> List[garak.attempt.Attempt]:
        return super().probe(generator)
