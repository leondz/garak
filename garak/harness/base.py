#!/usr/bin/env python3

import json
import logging

from colorama import Fore, Style

import _config
import _plugins


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


class ProbewiseHarness(Harness):
    def __init__(self):
        super().__init__()

    def run(self, model, probenames, evaluator):
        probenames = sorted(probenames)
        print("probe queue:", probenames)
        logging.info("probe queue: " + " ".join(probenames))
        for probename in probenames:
            try:
                probe = _plugins.load_plugin(probename)
            except Exception as e:
                print(f"failed to load probe {probename}")
                logging.warning(f"failed to load probe {probename}")
                continue
            detectors = []
            for detector_name in sorted(probe.recommended_detector):
                detector = _plugins.load_plugin(
                    "detectors." + detector_name, break_on_fail=False
                )
                if detector:
                    detectors.append(detector)
                else:
                    print(f" detector load failed: {detector_name}, skipping >>")
                    logging.error(
                        f" detector load failed: {detector_name}, skipping >>"
                    )
            h = Harness()
            h.run(model, [probe], detectors, evaluator, announce_probe=False)
            # del probe, h, detectors
