# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Base classes for probes.

Probe plugins must inherit one of these. `Probe` serves as a template showing
what expectations there are for inheriting classes. """

import copy
import json
import logging
from collections.abc import Iterable
from typing import Union

from colorama import Fore, Style
import tqdm

from garak import _config
import garak.attempt


class Probe:
    """Base class for objects that define and execute LLM evaluations"""

    # uri for a description of the probe (perhaps a paper)
    uri: str = ""
    # language this is for, in bcp47 format; * for all langs
    bcp47: Union[Iterable[str], None] = None
    # should this probe be included by default?
    active: bool = True
    # MISP-format taxonomy categories
    tags: Iterable[str] = []
    # what the probe is trying to do, phrased as an imperative
    goal: str = ""
    # Deprecated -- the detectors that should be run for this probe. always.Fail is chosen as default to send a signal if this isn't overridden.
    recommended_detector: Iterable[str] = ["always.Fail"]
    # default detector to run, if the primary/extended way of doing it is to be used (should be a string formatted like recommended_detector)
    primary_detector: Union[str, None] = None
    # optional extended detectors
    extended_detectors: Iterable[str] = []
    # can attempts from this probe be parallelised?
    parallelisable_attempts: bool = True
    # Keeps state of whether a buff is loaded that requires a call to untransform model outputs
    post_buff_hook: bool = False

    def __init__(self):
        """Sets up a probe. This constructor:
        1. populates self.probename based on the class name,
        2. logs and optionally prints the probe's loading,
        3. populates self.description based on the class docstring if not yet set"""
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
        """hook called when a new attempt is registered, allowing e.g.
        systematic transformation of attempts"""
        return attempt

    def _generator_precall_hook(self, generator, attempt=None):
        """function to be overloaded if a probe wants to take actions between
        attempt generation and posing prompts to the model"""
        pass

    def _buff_hook(
        self, attempts: Iterable[garak.attempt.Attempt]
    ) -> Iterable[garak.attempt.Attempt]:
        """this is where we do the buffing, if there's any to do"""
        if len(_config.buffmanager.buffs) == 0:
            return attempts
        buffed_attempts = []
        buffed_attempts_added = 0
        if _config.plugins.buffs_include_original_prompt:
            for attempt in attempts:
                buffed_attempts.append(attempt)
        for buff in _config.buffmanager.buffs:
            if (
                _config.plugins.buff_max is not None
                and buffed_attempts_added >= _config.plugins.buff_max
            ):
                break
            if buff.post_buff_hook:
                self.post_buff_hook = True
            for buffed_attempt in buff.buff(
                attempts, probename=".".join(self.probename.split(".")[-2:])
            ):
                buffed_attempts.append(buffed_attempt)
                buffed_attempts_added += 1
        return buffed_attempts

    @staticmethod
    def _postprocess_buff(attempt: garak.attempt.Attempt) -> garak.attempt.Attempt:
        """hook called immediately after an attempt has been to the generator,
        buff de-transformation; gated on self.post_buff_hook"""
        for buff in _config.buffmanager.buffs:
            if buff.post_buff_hook:
                attempt = buff.untransform(attempt)
        return attempt

    def _generator_cleanup(self):
        """Hook to clean up generator state"""
        self.generator.clear_history()

    def _postprocess_hook(
        self, attempt: garak.attempt.Attempt
    ) -> garak.attempt.Attempt:
        """hook called to process completed attempts; always called"""
        return attempt

    def _mint_attempt(self, prompt, seq=None) -> garak.attempt.Attempt:
        """function for creating a new attempt given a prompt"""
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
        """handles sending an attempt to the generator, postprocessing, and logging"""
        self._generator_precall_hook(self.generator, this_attempt)
        this_attempt.outputs = self.generator.generate(this_attempt.prompt)
        if self.post_buff_hook:
            this_attempt = self._postprocess_buff(this_attempt)
        this_attempt = self._postprocess_hook(this_attempt)
        _config.transient.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
        self._generator_cleanup()
        return copy.deepcopy(this_attempt)

    def probe(self, generator) -> Iterable[garak.attempt.Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug("probe execute: %s", self)

        self.generator = generator

        # build list of attempts
        attempts_todo: Iterable[garak.attempt.Attempt] = []
        prompts = list(self.prompts)
        for seq, prompt in enumerate(prompts):
            attempts_todo.append(self._mint_attempt(prompt, seq))

        # buff hook
        if len(_config.buffmanager.buffs) > 0:
            attempts_todo = self._buff_hook(attempts_todo)

        # iterate through attempts
        attempts_completed: Iterable[garak.attempt.Attempt] = []

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
