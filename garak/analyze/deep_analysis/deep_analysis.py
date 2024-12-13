# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Provide feedback, recommendations, and qualitative feedback on scan results.
"""

import json
from multiprocessing import Pool
from functools import lru_cache
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
from analytics import *

from garak.data import path as data_path


ANALYSIS_FILE = data_path / "deep_analysis" / "deep_analysis.csv"


@lru_cache
def load_scores(filepath: Path) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    return df


def get_position(probe_name: str, score: float, filepath: Path) -> int:
    """
    Get the position of a target's probe score in relation to other models in the bag

    Parameters
    ----------
    probe_name: str: Name of the probe
    score: float: Value of the score
    filepath: Path: Path to file containing the values of models in the bag

    Returns
    -------
    position: int: The position of the model in the set of sorted scores.
    """
    scores = load_scores(filepath)
    probe_scores = np.sort(scores[probe_name].to_numpy())
    position = int(np.where(probe_scores <= score)[0])
    return position


def tier_1(analysis_dict: dict) -> str:
    pass


def tier_2(analysis_dict: dict) -> str:
    pass


def deep_analysis(report_path, bag_path=ANALYSIS_FILE) -> Tuple[str, str]:
    """
    Take garak report jsonl file and perform qualitative analysis on the probe results for the target.

    Parameters
    ----------
    report_path: Path: Path to garak report file
    bag_path: Path: Path to csv file of model results in bag

    Returns
    -------

    """
    evals = dict()
    with open(report_path, "r", encoding="utf-8") as reportfile:
        for line in reportfile:
            record = json.loads(line.strip())
            if record["entry_type"] == "eval":
                probe = record["probe"].replace("probes.", "")
                detector = record["detector"].replace("detector.", "")
                score = record["passed"] / record["total"] if record["total"] else 0
                instances = record["total"]
                position = get_position(
                    probe_name=probe, score=score, filepath=bag_path
                )
                if probe not in evals.keys():
                    evals["probe"] = {
                        "detector": detector,
                        "score": score,
                        "instances": instances,
                        "position": position,
                    }

    # Tier 1 analysis
    tier_1_results = dict()
    for k, v in TIER_1_PROBE_GROUPS.items():
        tier_1_results[k] = dict()
        for probe_name in v:
            overall_score = evals[probe_name]["score"]
            overall_position = evals[probe_name]["position"]
            instances = evals[probe_name]["instances"]
            tier_1_results[k][probe_name] = {
                "score": overall_score,
                "position": overall_position,
                "instances": instances,
            }
    tier_1_analysis = tier_1(tier_1_results)

    # Tier 2 analysis
    tier_2_results = dict()
    for k, v in TIER_2_PROBE_GROUPS.items():
        tier_2_results[k] = dict()
        for probe_name in v:
            overall_score = evals[probe_name]["score"]
            overall_position = evals[probe_name]["position"]
            instances = evals[probe_name]["instances"]
            tier_2_results[k][probe_name] = {
                "score": overall_score,
                "position": overall_position,
                "instances": instances,
            }
    tier_2_analysis = tier_2(tier_2_results)

    return tier_1_analysis, tier_2_analysis
