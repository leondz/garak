#!/usr/bin/env python3

from colorama import Fore, Back, Style

class Evaluator:
    def __init__():
        messages = []
        self.probename = ""

    def test(self, test_value):
        return False # fail everything by default

    def evaluate(self, results, queries, probename=""):
        self.probename=probename
        for test_name in sorted(results.keys()):
            passes = [1 if self.test(r) else 0 for r in map(float, results[test_name])]
            self.print_results(test_name, passes, queries)

    def print_results(self, test_name, passes, messages):
        if len(passes):
            outcome = Fore.LIGHTRED_EX+'FAIL' if sum(passes)<len(passes) else Fore.LIGHTGREEN_EX+'PASS'
        else:
            outcome = Fore.LIGHTYELLOW_EX+'SKIP'
        print(f"{self.probename:<25}{test_name:>25} {Style.BRIGHT}{outcome}{Style.RESET_ALL},",
              f"ok on {sum(passes):>4}/{len(passes):>4}"
              )
        if messages:
            for i in range(len(passes)):
                if not passes[i]:
                    try:
                        print("❌", messages[i].strip().replace("\n", " "))
                    except:
                        pass

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
