#!/usr/bin/env python3

class Harness:
    def __init__(self):
        pass
    
    def run(self, model, probes, detectors, evaluator):

        for probe in probes:
            print('probe:', probe.name)
            generations = probe.probe(model)

            results = {}
            for t in detectors:
                results[t.name] = t.detect(generations)

            evaluator.evaluate(results)        