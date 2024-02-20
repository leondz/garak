#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Base classes for probes.

Probe plugins must inherit one of these. `Probe` serves as a template showing
what expectations there are for inheriting classes. """

import copy
import json
import logging
from collections.abc import Iterable
from typing import List

from colorama import Fore, Style
import tqdm

from garak import _config
import garak.attempt


class Probe:
    """Base class for objects that define and execute LLM evaluations"""

    uri = ""
    bcp47 = None  # language this is for, in bcp47 format; * for all langs
    recommended_detector = [
        "always.Fail"
    ]  # the detectors that should be run for this probe. always.Fail is chosen as default to send a signal if this isn't overridden
    active = True
    tags = []  # MISP-format taxonomy categories
    goal = ""  # what the probe is trying to do, phrased as an imperative
    primary_detector = None  # str default detector to run, if the primary/extended way of doing it is to be used (should be a string formatted like recommended_detector above)
    extended_detectors = []  # optional extended detectors
    parallelisable_attempts = True

    def __init__(self):
        self.probename = str(self.__class__).split("'")[1]
        if hasattr(_config.system, "verbose") and _config.system.verbose > 0:
            print(
                f"loading {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probe: {Style.RESET_ALL}{self.probename}"
            )
        logging.info("probe init: {self}")
        if "description" not in dir(self):
            if self.__doc__:
                self.description = self.__doc__.split("\n", maxsplit=1)[0]
            else:
                self.description = ""

    def _attempt_prestore_hook(
        self, attempt: garak.attempt.Attempt, seq: int
    ) -> garak.attempt.Attempt:
        return attempt

    def _generator_precall_hook(self, generator, attempt=None):
        """function to be overloaded if a probe wants to take actions between
        attempt generation and posing prompts to the model"""
        pass

    def _buff_hook(
        self, attempts: Iterable[garak.attempt.Attempt]
    ) -> Iterable[garak.attempt.Attempt]:
        """this is where we do the buffing, if there's any to do"""
        if (
            "buff_instances" not in dir(_config.transient)
            or len(_config.transient.buff_instances) == 0
        ):
            return attempts
        buffed_attempts = []
        for buff in _config.transient.buff_instances:
            for buffed_attempt in buff.buff(
                attempts, probename=".".join(self.probename.split(".")[-2:])
            ):
                buffed_attempts.append(buffed_attempt)
        return buffed_attempts

    def _postprocess_hook(
        self, attempt: garak.attempt.Attempt
    ) -> garak.attempt.Attempt:
        return attempt

    def _mint_attempt(self, prompt, seq=None) -> garak.attempt.Attempt:
        new_attempt = garak.attempt.Attempt()
        new_attempt.prompt = prompt
        new_attempt.probe_classname = (
            str(self.__class__.__module__).replace("garak.probes.", "")
            + "."
            + self.__class__.__name__
        )
        new_attempt.status = garak.attempt.ATTEMPT_STARTED
        new_attempt.goal = self.goal
        new_attempt.seq = seq
        new_attempt = self._attempt_prestore_hook(new_attempt, seq)
        return new_attempt

    def _execute_attempt(self, this_attempt):
        self._generator_precall_hook(self.generator, this_attempt)
        this_attempt.outputs = self.generator.generate(this_attempt.prompt)
        _config.transient.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
        this_attempt = self._postprocess_hook(this_attempt)
        return copy.deepcopy(this_attempt)

    def probe(self, generator) -> List[garak.attempt.Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug("probe execute: %s", self)

        self.generator = generator

        # build list of attempts
        attempts_todo = []
        prompts = list(self.prompts)
        for seq, prompt in enumerate(prompts):
            attempts_todo.append(self._mint_attempt(prompt, seq))

        # buff hook
        attempts_todo = self._buff_hook(attempts_todo)

        # iterate through attempts
        attempts_completed = []

        if (
            _config.system.parallel_attempts
            and _config.system.parallel_attempts > 1
            and self.parallelisable_attempts
            and len(attempts_todo) > 1
        ):
            from multiprocessing import Pool

            attempt_bar = tqdm.tqdm(total=len(attempts_todo), leave=False)
            attempt_bar.set_description(self.probename.replace("garak.", ""))

            with Pool(_config.system.parallel_attempts) as attempt_pool:
                for result in attempt_pool.imap_unordered(
                    self._execute_attempt, attempts_todo
                ):
                    attempts_completed.append(
                        result
                    )  # these will be out of original order
                    attempt_bar.update(1)

        else:
            attempt_iterator = tqdm.tqdm(attempts_todo, leave=False)
            attempt_iterator.set_description(self.probename.replace("garak.", ""))
            for this_attempt in attempt_iterator:
                attempts_completed.append(self._execute_attempt(this_attempt))

        logging.debug(
            "probe return: %s with %s attempts", self, len(attempts_completed)
        )

        return attempts_completed
