#!/usr/bin/env python
# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import re
import sys


def collapse_whitespace(s):
    return re.sub("[\s\t\n]+", " ", s)


print("\t".join("probe goal prompt output detector".split()))
with open(sys.argv[1], "r", encoding="utf-8") as hitlog_jsonl_file:
    for line in hitlog_jsonl_file:
        line = line.strip()
        if line:
            l = json.loads(line)
            print(
                "\t".join(
                    [
                        l["probe"],
                        l["goal"],
                        collapse_whitespace(l["prompt"]),
                        collapse_whitespace(l["output"]),
                        l["detector"],
                    ]
                )
            )
