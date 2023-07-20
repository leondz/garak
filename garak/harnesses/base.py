#!/usr/bin/env python3
"""Base harness

A harness coordinates running probes on a generator, running detectors on the 
outputs, and evaluating the results.

This module ncludes the class Harness, which all `garak` harnesses must 
inherit from.
"""


from collections import defaultdict
import json
import logging

from colorama import Fore, Style
import tqdm

from garak.attempt import *
import garak._config as _config


class Harness:
    """Class to manage the whole process of probing, detecting and evaluating"""

    active = True

    def __init__(self):
        logging.debug(f"harness run: {self}")

    def run(self, model, probes, detectors, evaluator, announce_probe=True) -> None:
        """Core harness method

        :param model: an instantiated generator providing an interface to the model to be examined
        :type model: garak.generators.Generator
        :param probes: a list of probe instances to be run
        :type probes: List[garak.probes.base.Probe]
        :param detectors: a list of detectors to use on the results of the probes
        :type detectors: List[garak.detectors.base.Detector]
        :param evaluator: an instantiated evaluator for judging detector results
        :type evaluator: garak.evaluators.base.Evaluator
        :param announce_probe: Should we print probe loading messages?
        :type announce_probe: bool, optional
        """
        if not detectors:
            logging.warning("No detectors, nothing to do")
            if _config.args and _config.args.verbose >= 2:
                print("No detectors, nothing to do")
            return None

        for probe in probes:
            logging.info("generating...")
            if not probe:
                continue
            attempt_results = probe.probe(model)

            eval_outputs, eval_results = [], defaultdict(list)
            first_detector = True
            for d in detectors:
                attempt_iterator = tqdm.tqdm(attempt_results, leave=False)
                detector_probe_name = d.detectorname.replace("garak.detectors.", "")
                attempt_iterator.set_description("detectors." + detector_probe_name)
                for attempt in attempt_iterator:
                    attempt.detector_results[detector_probe_name] = d.detect(attempt)

                    if first_detector:
                        eval_outputs += attempt.outputs
                    eval_results[detector_probe_name] += attempt.detector_results[
                        detector_probe_name
                    ]
                first_detector = False

            for attempt in attempt_results:
                attempt.status = ATTEMPT_COMPLETE
                _config.reportfile.write(json.dumps(attempt.as_dict()) + "\n")

            evaluator.evaluate(attempt_results)
