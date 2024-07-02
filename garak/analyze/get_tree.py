#!/usr/bin/env python

# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
import json
import sys

probes = set([])
node_info = defaultdict(dict)

with open(sys.argv[1], "r") as reportfile:
    for line in reportfile:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r["entry_type"] == "tree_data":
            probe = r["probe"]
            probes.add(probe)
            node_info[probe][r["node_id"]] = r


for probe in probes:
    print(f"============== {probe} ==============")

    node_children = defaultdict(list)
    for node in node_info[probe].values():
        node_children[node["node_parent"]].append(node["node_id"])

    # roots: those with parents not in node_info, or none
    roots = set([])
    for node in node_info[probe].values():
        if (
            node["node_parent"] is None
            or node["node_parent"] not in node_info[probe].keys()
        ):
            roots.add(node["node_id"])

    def print_tree(node_id, indent=0):
        forms = "" + ",".join(node_info[probe][node_id]["surface_forms"]) + ""
        print(
            "  " * indent + f"{forms} ::> {node_info[probe][node_id]['node_score']}",
        )
        children = node_children[node_id]
        if children:
            for child in children:
                print_tree(child, indent + 1)

    for root in sorted(list(roots)):
        print_tree(root)
