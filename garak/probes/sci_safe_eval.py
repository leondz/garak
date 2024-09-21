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

    # We should concatenate `hf_raw_base_url` before `hf_raw_filename` to get a final subdataset url
    hf_raw_base_url: str = "https://huggingface.co/datasets/Tianhao0x01/SciSafeEval/raw/main/"

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

class ChemistryMoleculeGeneration(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "chemistry_molecule-generation.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True, use_smiles=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<smiles/selfies>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            use_smiles (bool): If True, '<smiles/selfies>' will be replaced with 'smiles' data, otherwise 'selfies'.
        
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        smiles_or_selfies = json_obj['smiles'] if use_smiles else json_obj['selfies']
                        prompt = json_obj['instruction'].replace('<name>', json_obj['name']).replace('<smiles/selfies>', smiles_or_selfies)
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class ChemistryPropertyPrediction(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "chemistry_property-prediction.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True, use_smiles=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<smiles/selfies>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            use_smiles (bool): If True, '<smiles/selfies>' will be replaced with 'smiles' data, otherwise 'selfies'.
        
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        smiles_or_selfies = json_obj['smiles'] if use_smiles else json_obj['selfies']
                        prompt = json_obj['instruction'].replace('<name>', json_obj['name']).replace('<smiles/selfies>', smiles_or_selfies)
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class ChemistryReactionPrediction(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "chemistry_reaction-prediction.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True, use_smiles=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<smiles/selfies>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            use_smiles (bool): If True, '<smiles/selfies>' will be replaced with 'smiles' data, otherwise 'selfies'.
        
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        smiles_or_selfies = json_obj['smiles'] if use_smiles else json_obj['selfies']
                        prompt = json_obj['instruction'].replace('<name>', json_obj['name']).replace('<smiles/selfies>', smiles_or_selfies)
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class BiologyProteinFunctionPrediction(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "biology_protein-function-prediction.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class BiologyProteinStructureGeneration(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "biology_protein-structure-generation.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class BiologyProteinStructurePrediction(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "biology_protein-structure-prediction.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class BiologyGeneClassification(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "biology_gene-classification.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class BiologyGeneGeneration(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "biology_gene-generation.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]

class MedicineInferenceReasoning(SciSafeEval, Probe):
    # We should concatenate `hf_raw_filename` after `hf_raw_base_url` to get a final subdataset url
    hf_raw_filename: str = "medicine_inference-reasoning.jsonl"

    def read_sci_safe_eval(self, file_path, combine=True):
        """
        Reads JSONL data from a file and returns the processed data based on the combine option.
        
        Args:
            file_path (str): The path to the JSONL file.
            combine (bool): If True, replaces placeholders ('<name>', '<sequence>') in 'instruction'
                            with the corresponding data to form 'prompt'.
            
        Returns:
            list: A list of dictionaries containing either the combined 'prompt' or just the instruction.
        """
        data = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    json_obj = json.loads(line.strip())
                    
                    if combine:
                        # Replace placeholders with actual data
                        prompt = (json_obj['instruction']
                                .replace('<name>', json_obj['name'])
                                .replace('<sequence>', json_obj['sequence']))
                        
                        data.append({
                            "idx": json_obj['idx'],
                            "prompt": prompt,
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
                    else:
                        # Only return the instruction as is
                        data.append({
                            "idx": json_obj['idx'],
                            "instruction": json_obj['instruction'],
                            "few-shot": json_obj.get('few-shot', []),
                            "cot": json_obj.get('cot', None),
                            "jailbreak": json_obj.get('jailbreak', None),
                            "tags": json_obj.get('tags', [])
                        })
            
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
            # Make the directory if it doesn't exist
            os.makedirs(scisafeeval_data_dir)
        
        # Full path where the dataset should be saved
        hf_local_filepath = scisafeeval_data_dir / self.hf_raw_filename
        
        # Do the download if the file doesn't already exist
        if not os.path.exists(hf_local_filepath):
            hf_subdataset_url: str = self.hf_raw_base_url + self.hf_raw_filename
            response = requests.get(hf_subdataset_url)
            
            # Save the file to the specified location
            with open(hf_local_filepath, 'wb') as f:
                f.write(response.content)
        
        # Read the downloaded JSONL file and extract the prompts
        self.prompts = [
            prompt['prompt']
            for prompt in self.read_sci_safe_eval(hf_local_filepath)
        ]