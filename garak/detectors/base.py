#!/usr/bin/env python3

import logging
import re

from colorama import Fore, Style

from garak.harness.base import Attempt
from garak._config import args


class Detector:
    def __init__(self):
        if not self.name:
            self.name = __class__  # short name
        self.description = "Empty detector"
        self.uri = ""  # reference
        self.bcp47 = None  # language this is for, in bcp47 format
        self.precision = 0.0
        self.recall = 0.0
        self.accuracy = None
        self.detectorname = str(self.__class__).split("'")[1]
        if not args or args.verbose > 0:
            print(
                f"loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}detector{Style.RESET_ALL}: {self.detectorname}"
            )
        logging.info(f"detector init: {self}")

    def detect(self, attempt: Attempt):
        return [None] * len(attempt.outputs)


class HFDetector(Detector):
    def __init__(self, model_path, target_class):
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            TextClassificationPipeline,
        )

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

    def detect(self, attempt: Attempt):
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
    def __init__(self, substrings):
        super().__init__()
        self.substrings = substrings
        self.matchtype = "str"  # str or word

    def detect(self, attempt: Attempt, case_sensitive=False):
        detector_results = []
        for output in attempt.outputs:
            match = False
            for s in self.substrings:
                if self.matchtype == "str":
                    if case_sensitive:
                        if s in output:
                            match = True
                    else:
                        if s.lower() in output.lower():
                            match = True
                elif self.matchtype == "word":
                    s = re.escape(s)
                    if re.search(f"\\b{s}\\b", output):
                        match = True
                else:
                    raise ValueError(
                        f"Don't know how to process matchtype: {self.matchtype}"
                    )
            detector_results.append(1 if match else 0)

        return detector_results
