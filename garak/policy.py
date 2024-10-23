# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Policy point tools """

import importlib
import json
import logging
import re

from garak.data import path as data_path


class Policy:

    # policy.points[behaviour] -> dict of policy keys and True/False/None
    # policy.is_permitted[behaviour] -> True/False/None
    # policy.settree(prefix, value) -> set this and all sub-points in the policy to value
    # policy.parse_eval_result(eval_result) -> plug in to probes, load up results from an eval, build a policy
    # policy.compare(policy) -> list of policy points where there’s a difference

    # serialise & deserialise
    none_inherits_parent = True  # take parent policy if point value is None?
    default_point_policy = None
    permissive_root_policy = True

    def __init__(self) -> None:
        self.points = {}
        self._load_policy_points()

    def _load_policy_points(self, policy_data_path=None) -> None:
        """Populate the list of potential policy points given a policy structure description"""

        self.points = {}  # zero out the existing policy points
        for k in _load_policy_descriptions(policy_data_path=policy_data_path):
            self.points[k] = self.default_point_policy

    def is_permitted(self, point):
        if point not in self.points:
            raise ValueError("No policy point found for %s", point)

        if point == "":
            return self.permissive_root_policy is True

        point_policy = self.points[point]
        if point_policy is None and self.none_inherits_parent:
            return self.is_permitted(self.get_parent_name(point))

        return point_policy

    def settree(self, point, policy_value):
        points_to_set = [p for p in self.points if re.match(f"^{point}", p)]
        for point_to_set in points_to_set:
            p.points[point_to_set] = policy_value

    def parse_eval_result(self, eval_result):
        """get the result of a garak evaluation, and populate the policy based on this"""

        # strictness options:
        #  strict: any failure -> behaviour is permitted
        #  n failures: n or more failures -> behaviour is permitted
        #  threshold: >= threshold failure rate -> behaviour is permitted
        # let's run strict as default

        # flatten eval_result to a set/list of dicts
        # go through each one
        for result in _flatten_nested_policy_list(eval_result):
            # look in the probe for which policies are affected
            # we're going to make a decision on the policy

            module_name, probe_name = result["probe"].split(".")
            m = importlib.import_module(f"garak.probes.{module_name}")
            p_class = getattr(m, probe_name)
            if not hasattr(p_class, "policies"):
                logging.warning(
                    "policy: got policy result from probe {module_name}.{probe_name}, but probe class doesn't have 'policies' attrib"
                )
                continue

            points_affected = getattr(p_class, "policies")
            behaviour_permitted = any(
                [1 - n for n in result["passes"]]
            )  # passes of [0] means "one hit"
            for point_affected in points_affected:
                if point_affected in self.points:
                    self.points[point_affected] = (
                        behaviour_permitted  # NB this clobbers points if >1 probe tests a point
                    )
                else:
                    pass

    def get_parent_name(self, point):
        # structure A 000 a+
        # A is single-character toplevel entry
        # 000 is optional three-digit subcategory
        # a+ is text name of a subsubcategory
        if len(point) > 4:
            return point[:4]
        if len(point) == 4:
            return point[0]
        if len(point) == 1:
            return ""
        else:
            raise ValueError(
                "Invalid policy name %s. Should be a letter, plus optionally 3 digits, plus optionally some letters",
                point,
            )


def _load_policy_descriptions(policy_data_path=None) -> dict:
    if policy_data_path is None:
        policy_filepath = data_path / "policy" / "policy_typology.json"
    else:
        policy_filepath = data_path / policy_data_path
    with open(policy_filepath, "r", encoding="utf-8") as policy_file:
        return json.load(policy_file)


def _flatten_nested_policy_list(structure):
    for mid in structure:
        for inner in mid:
            for item in inner:
                assert isinstance(item, dict)
                yield item
