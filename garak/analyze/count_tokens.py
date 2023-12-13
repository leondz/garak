#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import sys

calls = 0
input_length = 0
output_length = 0
generations = 10

reportfile = open(sys.argv[1], encoding="utf-8")
for line in reportfile:
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if "run.generations" in r:
        generations = r["run.generations"]
        continue
    if "status" in r and r["status"] == 2:
        input_length += len(r["prompt"]) * generations
        calls += generations
        output_length += len("".join(r["outputs"]))

print(f"Calls: {calls}")
print(f"Input chars: {input_length}")
print(f"Output chars: {output_length}")
