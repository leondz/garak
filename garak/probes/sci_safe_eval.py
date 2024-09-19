#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Title: SCISAFEEVAL: A COMPREHENSIVE BENCHMARK FOR SAFETY ALIGNMENT OF SCIENTIFIC LARGE LANGUAGE MODELS
Paper: <arxiv link>
Code: https://github.com/DavidLee528/SciSafeEval
Dataset: <huggingface link>
Reference: <reference>
"""

import os
import logging

import requests
import tqdm
import json

from garak import _config
from garak.probes.base import Probe
from garak.generators.base import Generator


class SciSafeEval(Probe):
    """
    Title: SCISAFEEVAL: A COMPREHENSIVE BENCHMARK FOR SAFETY ALIGNMENT OF SCIENTIFIC LARGE LANGUAGE MODELS
    Paper: <arxiv link>
    Code: https://github.com/DavidLee528/SciSafeEval
    Dataset: <huggingface link>
    Reference: <reference>
    """

    active = True
    doc_uri = "<arxiv link>"
    bcp47 = "en"
    recommended_detector = ["refuse_to_answer.RefuseToAnswer"]
    tags = [
        "avid-effect:security:S0403",
        "avid-effect:performance:P0204",
        "owasp:llm01",
        "quality:Security:PromptStability",
        "payload:jailbreak",
    ]
    goal = "Let LLMs answer malicious scientific querys."

    prompts = []

    modality: dict = {"in": {"text"}}

    scisafeeval_dataset_catalog = (
        _config.transient.package_dir / "resources" / "scisafeeval_filenames.txt"
    )

    scisafeeval_dataset_filenames = []

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces '<content>' in 'instruction' with 'content' to form 'prompt'. 
                            If False, only 'content' is returned.
                            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just 'content'.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace '<content>' in 'instruction' with 'content'
                        prompt = json_obj['instruction'].replace('<content>', json_obj['content'])
                        data.append({"id": json_obj['id'], "prompt": prompt})
                    else:
                        # Only return 'content'
                        data.append({"id": json_obj['id'], "prompt": json_obj['content']})
            
            return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {file_path}")
            return None

    def _load_SciSafeEval(self):
        scisafeeval_data_dir = (
            _config.transient.cache_dir / "resources" / "SciSafeEval" / "SciSafeEval"
        )
        if not os.path.exists(scisafeeval_data_dir):
            # make the dir
            os.makedirs(scisafeeval_data_dir)
        # do the download
        # with open(self.safebench_image_catalog, "r", encoding="utf8") as _f:
        #     self.safebench_image_filenames = _f.read().strip().split("\n")
        # for filename in tqdm.tqdm(
        #     self.safebench_image_filenames,
        #     leave=False,
        #     desc=f"Downloading {self.__class__.__name__} images",
        # ):
        #     filepath = safebench_data_dir / filename
        #     if not os.path.isfile(filepath):
        #         uri = f"https://raw.githubusercontent.com/ThuCCSLab/FigStep/main/data/images/SafeBench/{filename}"
        #         with open(filepath, "wb") as f:
        #             f.write(requests.get(uri).content)

        
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval("/home/tianhao.li/research/garak/garak/resources/SciSafeEval/SciSafeEval/sample.jsonl")
        ]


    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._load_SciSafeEval()

    def probe(self, generator):
        if not isinstance(generator, Generator):
            raise ValueError("Incorrect class type of incoming argument `generator`.")
        if not generator.modality["in"] == self.modality["in"]:
            raise ValueError(
                f"Incorrect generator input modality {generator.modality['in']}, expect {self.modality['in']} for this probe."
            )

        return super().probe(generator)

