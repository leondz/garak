#!/usr/bin/env python3

import logging
import re
from typing import List

from colorama import Fore, Style

from garak.attempt import Attempt
from garak._config import args


class Detector:
    """Class defining a way of detecting a hit"""

    def __init__(self):
        if "name" not in dir(self):
            self.name = __class__  # short name
        if "description" not in dir(self):
            self.description = "Empty detector"
        if "uri" not in dir(self):
            self.uri = ""  # reference
        if "bcp47" not in dir(self):
            self.bcp47 = None  # language this is for, in bcp47 format
        if "precision" not in dir(self):
            self.precision = 0.0
        if "recall" not in dir(self):
            self.recall = 0.0
        if "accuracy" not in dir(self):
            self.accuracy = None
        if "detectorname" not in dir(self):
            self.detectorname = str(self.__class__).split("'")[1]
        if not args or args.verbose > 0:
            print(
                f"loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}detector{Style.RESET_ALL}: {self.detectorname}"
            )
        logging.info(f"detector init: {self}")

    def detect(self, attempt: Attempt) -> List[float]:
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

        if args:
            set_seed(args.seed)

        self.name = f"HF:{model_path}"
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

    def detect(self, attempt: Attempt) -> List[float]:
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

    def detect(self, attempt: Attempt, case_sensitive=False) -> List[float]:
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

    def detect(self, attempt: Attempt, case_sensitive=False) -> List[float]:
        detector_results = []
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
