#!/usr/bin/env python3

from collections import defaultdict
import json
import logging
import uuid

from colorama import Fore, Style

import garak._config as _config


class Harness:
    def __init__(self):
        pass

    def run(
        self, model, probes, detectors, evaluator, announce_probe=True
    ):  # pass list of objects
        if not detectors:
            logging.warning("No detectors, nothing to do")
            print("No detectors, nothing to do")
            return None

        for probe in probes:
            logging.info("generating...")
            attempt_results = probe.probe(model)

            eval_outputs, eval_results = [], defaultdict(list)
            first_detector = True
            for d in detectors:
                for attempt in attempt_results:
                    attempt.detector_results[d.name] = d.detect(attempt)
                    _config.reportfile.write(json.dumps(attempt.as_dict()) + "\n")

                    if first_detector:
                        eval_outputs += attempt.outputs
                    eval_results[d.name] += attempt.detector_results[d.name]
                first_detector = False
            evaluator.evaluate(eval_results, eval_outputs, probename=probe.probename)


class Attempt:
    def __init__(self) -> None:
        self.uuid = uuid.uuid4()
        self.prompt = None
        self.probe_classname = None
        self.probe_params = {}
        self.targets = None
        self.outputs = []
        self.notes = {}
        self.detector_results = {}

    def as_dict(self):
        return {
            "uuid": str(self.uuid),
            "probe_classname": self.probe_classname,
            "probe_params": self.probe_params,
            "targets": self.targets,
            "prompt": self.prompt,
            "outputs": self.outputs,
            "notes": self.notes,
            "detector_results": self.detector_results,
        }
