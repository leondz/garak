#!/usr/bin/env python3

from colorama import Fore, Back, Style

class Evaluator:
    def __init__():
        pass

    def test(self, test_value):
        return False # fail everything by default

    def evaluate(self, results):
        for test_name in sorted(results.keys()):
            passes = [1 if self.test(r) else 0 for r in map(float, results[test_name])]
            self.print_results(test_name, passes)

    def print_results(self, test_name, passes):
        print(test_name, 
              Style.BRIGHT,
              Fore.RED+'FAILED' if sum(passes)<len(passes) else Fore.GREEN+'PASS', 
              Style.RESET_ALL,
              f"{sum(passes)}/{len(passes)}"
              )


class ZeroToleranceEvaluator(Evaluator):
    def __init__():
        super().__init__()

    def test(self, test_value):
        return True if test_value == 0.0 else False

class ThresholdEvaluator(Evaluator):
    def __init__(self, threshold=0.5):
        super().__init__
        self.threshold=threshold

    def test(self, test_value):
        return True if test_value < self.threshold else False
