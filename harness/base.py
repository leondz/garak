#!/usr/bin/env python3

from colorama import Fore, Style

class Harness:
    def __init__(self):
        pass
    
    def run(self, model, probes, detectors, evaluator):

        for probe in probes:
            print('probe:', Style.BRIGHT+probe.name+Style.RESET_ALL)
            generations = probe.probe(model)

            results = {}
            for t in detectors:
                results[t.name] = t.detect(generations)

            evaluator.evaluate(results)
