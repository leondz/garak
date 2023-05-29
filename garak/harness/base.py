#!/usr/bin/env python3

from collections import defaultdict
import json
import logging

from colorama import Fore, Style

from garak.attempt import *
import garak._config as _config


class Harness:
    def __init__(self):
        pass

    def run(
        self, model, probes, detectors, evaluator, announce_probe=True
    ):  # pass list of objects
        if not detectors:
            logging.warning("No detectors, nothing to do")
            if _config.args and _config.args.verbose >= 2:
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

                    if first_detector:
                        eval_outputs += attempt.outputs
                    eval_results[d.name] += attempt.detector_results[d.name]
                first_detector = False

            for attempt in attempt_results:
                attempt.status = ATTEMPT_COMPLETE
                _config.reportfile.write(json.dumps(attempt.as_dict()) + "\n")

            evaluator.evaluate(eval_results, eval_outputs, probename=probe.probename)

