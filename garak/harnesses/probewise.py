#!/usr/bin/env python3
"""Probewise harness

Selects detectors to run for each probe based on that probe's recommendations
"""

import logging
from colorama import Fore, Style

from garak.harnesses.base import Harness

import garak._plugins as _plugins


class ProbewiseHarness(Harness):
    def __init__(self):
        super().__init__()

    def run(self, model, probenames, evaluator):
        """Execute a probe-by-probe scan

        Probes are executed in name order. For each probe, the detectors
        recommended by that probe are loaded and used to provide scores
        of the results. The detector(s) to be used are specified in the
        probe's ``recommended_detectors`` value; see :class:`garak.probes.base.Probe`
        for the defaults.

        :param model: an instantiated generator providing an interface to the model to be examined
        :type model: garak.generators.base.Generator
        :param probenames: a list of probe instances to be run
        :type probenames: List[garak.probes.base.Probe]
        :param evaluator: an instantiated evaluator for judging detector results
        :type evaluator: garak.evaluators.base.Evaluator
        """

        probenames = sorted(probenames)
        print(
            f"🕵️  queue of {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probes:{Style.RESET_ALL} "
            + ", ".join([name.replace("probes.", "") for name in probenames])
        )
        logging.info("probe queue: " + " ".join(probenames))
        for probename in probenames:
            try:
                probe = _plugins.load_plugin(probename)
            except Exception as e:
                print(f"failed to load probe {probename}")
                logging.warning(f"failed to load probe {probename}: {e}")
                continue
            if not probe:
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
