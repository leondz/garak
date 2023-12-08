#!/usr/bin/env python3

import sys
import json

started_attempt_uuids = set([])
completed_attempt_uuids = set([])

completed_attempts = {}

current_probe_classname = None

with open(sys.argv[1], "r", encoding="utf-8") as reportfile:
    for i, line in enumerate(reportfile):
        line = line.strip()
        if not line:
            continue

        record = json.loads(line)

        if not isinstance(record, dict):
            continue

        if "entry_type" not in record.keys():
            continue

        if record["entry_type"] in ("config", "init"):
            print("##", line)
            continue

        elif record["entry_type"] == "attempt":
            if record["status"] == 1:  # started
                started_attempt_uuids.add(record["uuid"])
                continue

            if record["status"] == 2:
                completed_attempt_uuids.add(record["uuid"])

            if record["probe_classname"] != current_probe_classname:
                print("## PROBE:", record["probe_classname"])
                current_probe_classname = record["probe_classname"]

            # for each detector:
            for detector_name, detector_scores in record["detector_results"].items():
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
                                repr(record["prompt"]),
                            ]
                        )
                    )
        elif record["entry_type"] == "eval":
            print(
                "\t".join(
                    map(
                        str,
                        [
                            record["probe"],
                            record["detector"],
                            "%0.4f" % (record["passed"] / record["total"]),
                            record["total"],
                        ],
                    )
                )
            )

if not started_attempt_uuids:
    print("## no attempts in log")
else:
    completion_rate = len(completed_attempt_uuids) / len(started_attempt_uuids)
    print("##", len(started_attempt_uuids), "attempts started")
    print("##", len(completed_attempt_uuids), "attempts completed")
    print(f"## attempt completion rate {completion_rate:.0%}")
