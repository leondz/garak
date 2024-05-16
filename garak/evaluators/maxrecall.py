"""maxrecall evaluator

deprecated

Should register a complete failure if there are any failures
"""

from garak.evaluators.base import Evaluator


class MaxRecallEvaluator(Evaluator):
    def __init__():
        super().__init__()

    def evaluate(self, results):
        for test in results.keys().sorted():
            no_failures = True
            if map(float, results[test]) != [0.0] * len(results[test]):
                no_failures = False

            print(test, "PASSED" if no_failures else "FAILED")
