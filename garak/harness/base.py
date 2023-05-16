#!/usr/bin/env python3

from colorama import Fore, Style

import _plugins

class Harness:
    def __init__(self):
        pass
    
    def run(self, model, probes, detectors, evaluator, announce_probe=True):

        for probe in probes:
            if announce_probe:
                print('loading probe:', Style.BRIGHT+probe.name+Style.RESET_ALL)
            print(f' -- probing {model.name}')
            generations = probe.probe(model)

            results = {}
            for t in detectors:
                results[t.name] = t.detect(generations)

            evaluator.evaluate(results, generations)

class ProbewiseHarness(Harness):
    def __init__(self):
        super().__init__()
    
    def run(self, model, probenames, evaluator):
        
        for probename in sorted(probenames):
            probe =_plugins.load_plugin(probename)
            print('loading probe:', Style.BRIGHT+probe.name+Style.RESET_ALL)
            detectors = []
            for detector_name in sorted(probe.recommended_detector):
                detector = _plugins.load_plugin('detectors.'+detector_name, break_on_fail=False)
                if detector:
                    detectors.append(detector)
            h = Harness()
            h.run(model, [probe], detectors, evaluator, announce_probe=False)