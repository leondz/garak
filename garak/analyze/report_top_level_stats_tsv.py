#!/usr/bin/env python

# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import json
import re
import sys


def collapse_whitespace(s):
    return re.sub("[\s\t\n]+", " ", s)


print(
    "\t".join(
        "probe probe_goal detector pass_rate attack_success_rate prompt_count".split()
    )
)
with open(sys.argv[1], "r", encoding="utf-8") as report_jsonl_file:
    for line in report_jsonl_file:
        line = line.strip()
        if line:
            l = json.loads(line)
            if l["entry_type"] == "eval":
                probe_plugin, probe_classname = l["probe"].split(".")
                probe_module = importlib.import_module("garak.probes." + probe_plugin)
                probe_class = getattr(probe_module, probe_classname)
                probe_goal = probe_class.goal
                prompt_count = l["total"]
                pass_rate = float(l["passed"]) / float(l["total"])
                asr = 1 - pass_rate

                print(
                    "\t".join(
                        map(
                            str,
                            [
                                l["probe"],
                                probe_goal,
                                l["detector"],
                                pass_rate,
                                asr,
                                prompt_count,
                            ],
                        )
                    )
                )
