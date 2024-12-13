# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Qualitative analytics by group for categories of probes
"""

import json
from functools import lru_cache
import numpy as np
from garak.data import path as data_path


TIER_1_PROBE_GROUPS = {
    "jailbreak": [
        "dan.DanInTheWild",
        "dan.DanInTheWildMini",
        "grandma.Slurs",
        "grandma.Substances",
        "latentinjection.LatentInjectionFactSnippetEiffel",
        "latentinjection.LatentInjectionReport",
        "latentinjection.LatentInjectionResume",
        "latentinjection.LatentInjectionTranslationEnFr",
        "latentinjection.LatentInjectionTranslationEnZh",
        "latentinjection.LatentJailbreak",
        "latentinjection.LatentJailbreakMini",
    ],
    "system": [
        "ansiescape.AnsiRaw",
        "latentinjection.LatentInjectionFactSnippetEiffel",
        "xss.MarkdownImageExfil",
        "fileformats.HF_Files",
    ],
    "tokenizer": ["goodside.Tag"],
    "code": [
        "packagehallucination.JavaScript",
        "packagehallucination.Python",
        "packagehallucination.Ruby",
        "packagehallucination.Rust",
    ],
    "misleading": [],
    "training_data": [
        "leakreplay.GuardianComplete",
        "leakreplay.LiteratureComplete",
        "leakreplay.LiteratureComplete80",
        "leakreplay.NYTComplete",
        "leakreplay.PotterComplete",
    ],
    "harm": ["grandma.Slurs", "grandma.Substances", "realtoxicityprompts.RTPBlank"],
    "bypass": [
        "encoding.InjectBase64",
        "encoding.InjectQP",
        "encoding.InjectUU",
        "goodside.Tag",
    ],
}

TIER_1_PROBES = list(set().union(TIER_1_PROBE_GROUPS.values()))

TIER_2_PROBE_GROUPS = {
    "jailbreak": [
        "dan.Ablation_Dan_11_0",
        "dan.AutoDAN",
        "dan.AutoDANCached",
        "goodside.ThreatenJSON",
        "promptinject.HijackHateHumans",
        "promptinject.HijackHateHumansMini",
        "promptinject.HijackKillHumans",
        "promptinject.HijackKillHumansMini",
        "promptinject.HijackLongPrompt",
        "promptinject.HijackLongPromptMini",
        "suffix.BEAST",
        "suffix.GCG",
        "suffix.GCGCached",
        "tap.PAIR",
        "tap.TAP",
        "tap.TAPCached",
        "visual_jailbreak.FigStep",
        "visual_jailbreak.FigStepTiny",
    ],
    "system": [],
    "tokenizer": [],
    "code": [
        "malwaregen.Evasion",
        "malwaregen.Payload",
        "malwaregen.SubFunctions",
        "malwaregen.TopLevel",
    ],
    "misleading": [
        "goodside.WhoIsRiley",
        "misleading.FalseAssertion50",
        "snowball.GraphConnectivity",
        "snowball.GraphConnectivityMini",
    ],
    "training_data": [
        "grandma.Win10",
        "grandma.Win11",
        "leakreplay.GuardianCloze",
        "leakreplay.LiteratureCloze",
        "leakreplay.LiteratureCloze80",
        "leakreplay.NYTCloze",
        "leakreplay.PotterCloze",
        "divergence.Repeat",
        "divergence.RepeatExtended",
    ],
    "harm": [
        "atkgen.Tox",
        "continuation.ContinueSlursReclaimedSlurs",
        "continuation.ContinueSlursReclaimedSlursMini",
        "lmrc.Bullying",
        "lmrc.Deadnaming",
        "lmrc.QuackMedicine",
        "lmrc.SexualContent",
        "lmrc.Sexualisation",
        "lmrc.SlurUsage",
        "topic.WordnetControversial",
    ],
    "bypass": [
        "encoding.InjectAscii85",
        "encoding.InjectBase16",
        "encoding.InjectBase2048",
        "encoding.InjectBase32",
        "encoding.InjectBraille",
        "encoding.InjectEcoji",
        "encoding.InjectHex",
        "encoding.InjectMime",
        "encoding.InjectMorse",
        "encoding.InjectNato",
        "encoding.InjectROT13",
        "encoding.InjectZalgo",
    ],
}

TIER_2_PROBES = list(set().union(TIER_2_PROBE_GROUPS.values()))

CALIBRATION_DATA = data_path / "calibration" / "calibration.json"

JAILBREAK_FEEDBACK_LOCATION = data_path / "deep_analysis" / "jailbreak.json"


@lru_cache
def load_calibration_data(calibration_filename=CALIBRATION_DATA):
    with open(calibration_filename, "r", encoding="utf-8") as f:
        data = json.loads(f.read().strip())

    probe_data = {key.split("/")[0]: value for key, value in data.items()}
    aggregate_scores = dict()
    for k, v in TIER_1_PROBE_GROUPS.items():
        scores = [probe_data[probe]["mu"] for probe in v if probe in probe_data.keys()]
        minus_sigma_scores = [
            probe_data[probe]["mu"] - probe_data[probe]["sigma"]
            for probe in v
            if probe in probe_data.keys()
        ]
        plus_sigma_scores = [
            probe_data[probe]["mu"] + probe_data[probe]["sigma"]
            for probe in v
            if probe in probe_data.keys()
        ]
        avg_score = float(np.average(scores)) if scores else 0.0
        low_score = float(np.average(minus_sigma_scores)) if minus_sigma_scores else 0.0
        high_score = float(np.average(plus_sigma_scores)) if plus_sigma_scores else 0.0
        aggregate_scores[k] = {
            "average": avg_score,
            "low": low_score,
            "high": high_score,
        }
    return data


def load_feedback(feedback_type: str) -> dict:
    match feedback_type:
        case "jailbreak":
            with open(JAILBREAK_FEEDBACK_LOCATION, "r", encoding="utf-8") as f:
                feedback = json.loads(f.read().strip())

        case _:
            feedback = dict()
    return feedback


def daninthewild_feedback(results: dict) -> str:
    # Currently returns nothing, as we do not have a bag written.
    return ""


def jailbreak(results: dict) -> str:
    feedback = ""
    calibration_data = load_calibration_data()
    jailbreak_thresholds = calibration_data["jailbreak"]
    avg_score = np.average([d["score"] for d in results.values()])
    jailbreak_feedback = load_feedback("jailbreak")
    match avg_score:
        case avg_score if avg_score >= jailbreak_thresholds["high"]:
            feedback = jailbreak_feedback["caution"]
        case avg_score if jailbreak_thresholds[
            "average"
        ] < avg_score < jailbreak_thresholds["high"]:
            feedback = jailbreak_feedback["above_average"]
        case avg_score if jailbreak_thresholds[
            "low"
        ] < avg_score <= jailbreak_thresholds["average"]:
            feedback = jailbreak_feedback["good"]
        case avg_score if 20 < avg_score <= jailbreak_thresholds["low"]:
            feedback = jailbreak_feedback["poor"]
        case _:
            feedback = jailbreak_feedback["caution_low"]
    # DanInTheWild/DanInTheWildMini gets its own callout
    if "dan.DanInTheWild" in results.keys():
        feedback += daninthewild_feedback(results["dan.DanInTheWild"])
    elif "dan.DanInTheWildMini" in results.keys():
        feedback += daninthewild_feedback(results["dan.DanInTheWildMini"])

    return feedback


def system(results: dict, tier: str) -> str:
    pass


def tokenizer(results: dict, tier: str) -> str:
    pass


def code(results: dict, tier: str) -> str:
    pass


def misleading(results: dict, tier: str) -> str:
    pass


def training_data(results: dict, tier: str) -> str:
    pass


def harm(results: dict, tier: str) -> str:
    pass


def bypass(results: dict, tier: str) -> str:
    pass
