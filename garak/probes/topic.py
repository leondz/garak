#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Topic probe

Attempt to get a model to engage on a number of contentious topics
"""

import logging
from typing import List

from garak import _config
from garak.probes.base import Probe
from garak.attempt import Attempt


class StackingProbe(Probe):
    active = False

    def _get_more_prompts(self) -> List[str]:
        return []

    def probe(self, generator) -> List[Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug("probe execute: %s", self)

        self.generator = generator

        # build list of attempts
        attempts_todo = []
        prompts = list(self.prompts)
        for seq, prompt in enumerate(prompts):
            attempts_todo.append(self._mint_attempt(prompt, seq))

        ## yoooooo let's do some kind of check around here? this is in the loop? i guess?

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


class TopicExplorerWordnet(Probe):
    """Explore which topics a model will respond to or deflect"""

    bcp47 = "*"
    primary_detector = "mitigation.MitigationBypass"
    goal = "get the model to engage off-topic"
    tags = [
        "avid-effect:security:S0301",
        "owasp:llm10",
        "owasp:llm06",
        "quality:Security:Confidentiailty",
    ]  # MISP-format taxonomy categories

    def __init__(self, config_root=...):
        self.target_topics = ["drugs"]

        super().__init__(config_root)