#!/usr/bin/env python3

import json
import logging

from colorama import Fore, Style

import _config


class Harness:
    def __init__(self):
        pass

    def run(self, model, probes, detectors, evaluator, announce_probe=True):
        if not detectors:
            logging.warning("No detectors, nothing to do")
            print("No detectors, nothing to do")
            return None

        for probe in probes:
            probename = str(probe.__class__).split("'")[1]
            print("generating...")
            logging.info("generating...")
            generations = probe.probe(model)

            results = {}
            for d in detectors:
                results[d.name] = d.detect(generations)
                for entry in zip(generations, results[d.name]):
                    report_line = {
                        "probe": probename,
                        "output": entry[0],
                        "detector": d.name,
                        "score": entry[1],
                    }
                    _config.reportfile.write(json.dumps(report_line) + "\n")

            evaluator.evaluate(
                results, generations, probename=".".join(probename.split(".")[1:])
            )
