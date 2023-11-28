#!/usr/bin/env python3
"""Base detectors.

These detectors show expectations and operations of any detector implemented 
in `garak`. `garak` detectors must inherit from a class in here."""


import logging
import re
from typing import List

from colorama import Fore, Style

import garak.attempt
from garak import _config


class Detector:
    """Base class for objects that define a way of detecting a probe hit / LLM failure"""

    uri = ""  # reference
    bcp47 = None  # language this is for, in bcp47 format
    precision = 0.0
    recall = 0.0
    accuracy = None
    active = True
    tags = []  # list of taxonomy categories per the MISP format

    def _set_description(self):
        if "description" not in dir(self):
            self.description = self.__doc__.split("\n")[0]

    def __init__(self):
        if "name" not in dir(self):
            self.name = __class__  # short name
        self.detectorname = str(self.__class__).split("'")[1]
        self._set_description()
        if hasattr(_config.system, "verbose") and _config.system.verbose > 0:
            print(
                f"loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}detector{Style.RESET_ALL}: {self.detectorname}"
            )
        logging.info(f"detector init: {self}")

    def detect(self, attempt: garak.attempt.Attempt) -> List[float]:
        """Takes a list of Attempts; classifies them; returns a list of results
        in the range 0.0-1.0 where 0.0 represents no hit, 1.0 represents successful hit
        (i.e. vulnerability found)."""
        return [None] * len(attempt.outputs)


class HFDetector(Detector):
    """Detector using a Hugging Face model"""

    def __init__(self, model_path, target_class):
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            TextClassificationPipeline,
            set_seed,
        )

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        self.name = f"HF: {model_path}"
        super().__init__()

        self.detector_model_path = model_path
        self.detector_target_class = target_class

        self.detector_model = AutoModelForSequenceClassification.from_pretrained(
            self.detector_model_path
        )
        self.detector_tokenizer = AutoTokenizer.from_pretrained(
            self.detector_model_path
        )
        self.detector = TextClassificationPipeline(
            model=self.detector_model, tokenizer=self.detector_tokenizer
        )

        self.graceful_fail = False

    def detect(self, attempt: garak.attempt.Attempt) -> List[float]:
        try:
            detector_raw_results = self.detector(
                attempt.outputs, **self.tokenizer_kwargs
            )
        except Exception as e:
            if self.graceful_fail:
                print(e)
                return []
            else:
                raise Exception() from e

        detector_results = []
        for d in detector_raw_results:
            detector_results.append(
                (1 - d["score"]) / 2
                if d["label"] != self.detector_target_class
                else (1 + d["score"]) / 2
            )

        return detector_results


class StringDetector(Detector):
    """Subclass of Detector using list of substrings as detection triggers"""

    def __init__(self, substrings):
        super().__init__()
        self.substrings = substrings
        self.matchtype = "str"  # str or word

    def detect(
        self, attempt: garak.attempt.Attempt, case_sensitive=False
    ) -> List[float]:
        detector_results = []
        for output in attempt.outputs:
            match = False
            for s in self.substrings:
                if case_sensitive:
                    s, output = s.lower(), output.lower()

                if self.matchtype == "str":
                    if s in output:
                        match = True
                elif self.matchtype == "word":
                    if re.search(r"\b" + s + r"\b", output):
                        match = True
                else:
                    raise ValueError(
                        f"Don't know how to process matchtype: {self.matchtype}"
                    )
            detector_results.append(1 if match else 0)

        return detector_results


class TriggerListDetector(Detector):
    """Subclass of Detector using attempt's notes[triggers] as list of strings to match"""

    def __init__(self):
        super().__init__()

    def detect(
        self, attempt: garak.attempt.Attempt, case_sensitive=False
    ) -> List[float]:
        detector_results = []
        if "triggers" in attempt.notes:
            triggers = attempt.notes["triggers"]
            for output in attempt.outputs:
                match = False
                for trigger in triggers:
                    if case_sensitive:
                        if trigger in output:
                            match = True
                    else:
                        if trigger.lower() in output.lower():
                            match = True
                detector_results.append(1 if match else 0)

        return detector_results
