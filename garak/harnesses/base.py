# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Base harness

A harness coordinates running probes on a generator, running detectors on the 
outputs, and evaluating the results.

This module ncludes the class Harness, which all `garak` harnesses must 
inherit from.
"""


from collections import defaultdict
import json
import logging
from typing import List

import tqdm

import garak.attempt
from garak import _config
from garak import _plugins


class Harness:
    """Class to manage the whole process of probing, detecting and evaluating"""

    active = True

    def __init__(self):
        logging.info("harness init: %s", self)

    def _load_buffs(self, buff_names: List) -> None:
        """Instantiate specified buffs into global config

        Inheriting classes call _load_buffs in their run() methods. They then call
        garak.harness.base.Harness.run themselves, and so if _load_buffs() is called
        from this base class, we'll end up w/ inefficient reinstantiation of buff
        objects. If one wants to use buffs directly with this harness without
        subclassing, then call this method instance directly.

        Don't use this in the base class's run method, garak.harness.base.Harness.run;
        harnesses should be explicit about how they expect to deal with buffs.
        """

        _config.buffmanager.buffs = []
        for buff_name in buff_names:
            err_msg = None
            try:
                _config.buffmanager.buffs.append(_plugins.load_plugin(buff_name))
                logging.debug("loaded %s", buff_name)
            except ValueError as ve:
                err_msg = f"❌🦾 buff load error:❌ {ve}"
            except Exception as e:
                err_msg = f"❌🦾 failed to load buff {buff_name}:❌ {e}"
            finally:
                if err_msg is not None:
                    print(err_msg)
                    logging.warning(err_msg)
                    continue

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
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print("No detectors, nothing to do")
            return None

        if not probes:
            logging.warning("No probes, nothing to do")
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print("No probes, nothing to do")
            return None

        for probe in probes:
            logging.debug("harness: probe start for %s", probe.probename)
            if not probe:
                continue
            attempt_results = probe.probe(model)
            assert isinstance(attempt_results, list)

            eval_outputs, eval_results = [], defaultdict(list)
            first_detector = True
            for d in detectors:
                logging.debug("harness: run detector %s", d.detectorname)
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
                attempt.status = garak.attempt.ATTEMPT_COMPLETE
                _config.transient.reportfile.write(json.dumps(attempt.as_dict()) + "\n")

            if len(attempt_results) == 0:
                logging.warning(
                    "zero attempt results: probe %s, detector %s",
                    probe.probename,
                    detector_probe_name,
                )
            else:
                evaluator.evaluate(attempt_results)

        logging.debug("harness: probe list iteration completed")
