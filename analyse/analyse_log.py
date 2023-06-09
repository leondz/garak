#!/usr/bin/env python3

import sys
import json

started_attempt_uuids = set([])
completed_attempt_uuids = set([])

completed_attempts = {}

current_probe_classname = None

with open(sys.argv[1], "r") as reportfile:
    for i, line in enumerate(reportfile):
        line = line.strip()
        if i == 0:
            print("##", line)
            continue

        if not line:
            continue

        attempt = json.loads(line)
        if isinstance(attempt, str):
            continue

        if "status" not in attempt.keys():
            continue

        if attempt["status"] == 1:  # started
            started_attempt_uuids.add(attempt["uuid"])
            continue

        if attempt["status"] == 2:
            completed_attempt_uuids.add(attempt["uuid"])

        if attempt["probe_classname"] != current_probe_classname:
            print("PROBE:", attempt["probe_classname"])
            current_probe_classname = attempt["probe_classname"]

        # for each detector:
        for detector_name, detector_scores in attempt["detector_results"].items():
            normalised_scores = [1 if i >= 0.5 else 0 for i in detector_scores]
            # are there any hits?
            if sum(normalised_scores):
                # if so print prompt & hit rate
                # i guess make this sortable so give probe, detector, hit rate, prompt
                hit_rate = sum(normalised_scores) / len(normalised_scores)
                print(
                    "\t".join(
                        [
                            current_probe_classname,
                            detector_name,
                            f"{hit_rate:0.2%}",
                            repr(attempt["prompt"]),
                        ]
                    )
                )

if not started_attempt_uuids:
    print("## no attempts in log")
else:
    completion_rate = len(completed_attempt_uuids) / len(started_attempt_uuids)
    print("##", len(started_attempt_uuids), "attempts started")
    print("##", len(completed_attempt_uuids), "attempts completed")
    print(f"## attempt completion rate {completion_rate:.0%}")
