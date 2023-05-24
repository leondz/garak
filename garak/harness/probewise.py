#!/usr/bin/env python3

import logging

from garak.harness.base import Harness

import garak._plugins as _plugins


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
                logging.warning(f"failed to load probe {probename}: {e}")
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
