# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import re
import sys


def collapse_whitespace(s):
    return re.sub("[\s\t\n]+", " ", s)


with open(sys.argv[1], "r", encoding="utf-8") as report_jsonl_file:
    for line in report_jsonl_file:
        line = line.strip()
        if line:
            l = json.loads(line)
            if (
                l["entry_type"] == "attempt" and l["status"] == 2
            ):  # only completed attempts:
                probe = l["probe_classname"]
                prompt = l["prompt"]
                outputs = l["outputs"]
                detector_results = l["detector_results"]
                detector = next(iter(detector_results))
                detector_scores = detector_results[detector]
                for i in range(len(outputs)):
                    print(
                        "\t".join(
                            [
                                probe,
                                prompt,
                                collapse_whitespace(outputs[i]),
                                detector,
                                str(detector_scores[i]),
                            ]
                        )
                    )
