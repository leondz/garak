#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NeMo LLM interface"""

import json
import os

import backoff
import nemollm
import tqdm

import garak._config
from garak.generators.base import Generator


class NeMoGenerator(Generator):
    generator_family_name = "NeMo"
    temperature = 1
    top_p = 1.0
    repetition_penalty = 1.1  # between 1 and 2 incl., or none

    def __init__(self, name=None, generations=10):
        self.name = name
        self.fullname = f"NeMo {self.name}"
        self.seed = garak._config.seed
        self.api_host = "https://api.llm.ngc.nvidia.com/v1"

        super().__init__(name, generations=generations)

        self.api_key = os.getenv("NGC_API_KEY", default=None)
        if self.api_key is None:
            raise ValueError(
                'Put the NGC API key in the NGC_API_KEY environment variable (this was empty)\n \
                e.g.: export NGC_API_TOKEN="xXxXxXxXxXxXxXxXxXxX"'
            )
        self.org_id = os.getenv("ORG_ID")

        if self.org_id is None:
            raise ValueError(
                'Put your org ID in the ORG_ID environment variable (this was empty)\n \
                e.g.: export NGC_API_TOKEN="xXxXxXxXxXxXxXxXxXxX"\n \
                Check "view code" on https://llm.ngc.nvidia.com/playground to see the ID'
            )

        self.nemo = nemollm.api.NemoLLM(
            api_host=self.api_host, api_key=self.api_key, org_id=self.org_id
        )

        if self.name is None:
            print(json.dumps(self.nemo.list_models(), indent=2))
            raise ValueError("Please specify a NeMo model - see list above")

    @backoff.on_exception(
        backoff.fibo,
        (nemollm.error.ServerSideError, nemollm.error.TooManyRequestsError),
        max_value=70,
    )
    def _call_api(self, prompt):
        # avoid:
        #    doesn't match schema #/components/schemas/CompletionRequestBody: Error at "/prompt": minimum string length is 1
        if prompt == "":
            return ""

        response = self.nemo.generate(
            model=self.name,
            prompt=prompt,
            tokens_to_generate=self.max_tokens,
            temperature=self.temperature,
            random_seed=self.seed,
            top_p=1.0,
            top_k=2,
            # stop=["\n"],
            repetition_penalty=self.repetition_penalty,
            beam_search_diversity_rate=0.0,
            beam_width=1,
            length_penalty=1.0,
        )
        return response["text"]

    def generate(self, prompt):
        outputs = []
        generation_iterator = tqdm.tqdm(list(range(self.generations)), leave=False)
        generation_iterator.set_description(
            self.fullname[:55]
        )  # replicate names are long incl. hash
        for i in generation_iterator:
            outputs.append(self._call_api(prompt))
        return outputs


default_class = "NeMoGenerator"
