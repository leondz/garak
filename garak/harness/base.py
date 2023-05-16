#!/usr/bin/env python3

from colorama import Fore, Style

import _plugins

class Harness:
    def __init__(self):
        pass
    
    def run(self, model, probes, detectors, evaluator, announce_probe=True):

        if not detectors:
            return None

        for probe in probes:
            if announce_probe:
                print(f'loading probe: {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{probe.name}{Style.RESET_ALL}')
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
                else:
                    print(f"❌ detector load failed: {detector_name}, skipping")
            h = Harness()
            h.run(model, [probe], detectors, evaluator, announce_probe=False)