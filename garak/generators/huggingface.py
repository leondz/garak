#!/usr/bin/env python3

import logging
import re
import os
from typing import List
import warnings

import backoff

from garak._config import args
from garak.generators.base import Generator


models_to_deprefix = ["gpt2"]
hf_max_new_tokens = 150


class HFRateLimitException(Exception):
    pass


class HFLoadingException(Exception):
    pass


class Local(Generator):
    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        self.generator_family_name = "Hugging Face 🤗"
        super().__init__(name)

        from transformers import pipeline, set_seed

        set_seed(args.seed)

        logging.info("generator init: {self}")
        import torch.cuda

        if torch.cuda.is_available() == False:
            logging.debug("Using CPU, torch.cuda.is_available() returned False")
            device = -1

        self.generator = pipeline(
            "text-generation",
            model=name,
            do_sample=do_sample,
            device=device,
        )
        self.deprefix_prompt = name in models_to_deprefix
        self.max_new_tokens = hf_max_new_tokens

    def generate(self, prompt):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            try:
                raw_output = self.generator(
                    prompt,
                    pad_token_id=self.generator.tokenizer.eos_token_id,
                    max_new_tokens=self.max_new_tokens,
                    num_return_sequences=self.generations,
                    # max_length = 1024,
                )
            except:
                raw_output = []  # could handle better than this..
        generations = [
            i["generated_text"] for i in raw_output
        ]  # generator returns 10 outputs by default in __init__
        if not self.deprefix_prompt:
            return generations
        else:
            return [re.sub("^" + re.escape(prompt), "", i) for i in generations]


class InferenceAPI(Generator):
    def __init__(self, name="", generations=10):
        self.fullname, self.name = name, name
        self.generator_family_name = "Hugging Face 🤗 Inference API"
        super().__init__(name, generations)

        self.api_url = "https://api-inference.huggingface.co/models/gpt2"
        self.api_token = os.getenv("HF_INFERENCE_TOKEN", default=None)
        if self.api_token:
            self.headers = {"Authorization": f"Bearer {self.api_token}"}
        else:
            self.headers = {}
            message = " ⚠️  No Hugging Face Inference API token in HF_INFERENCE_TOKEN, expect heavier rate-limiting"
            print(message)
            logging.info(message)
        self.deprefix = True
        self.max_new_tokens = hf_max_new_tokens

    @backoff.on_exception(
        backoff.fibo, (HFRateLimitException, HFLoadingException), max_value=125
    )
    def _call_api(self, prompt: str) -> List[str]:
        import json
        import requests

        self.wait_for_model = False

        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": not self.deprefix,
                "num_return_sequences": self.generations,
                "max_new_tokens": self.max_new_tokens,
            },
            "options": {
                "wait_for_model": self.wait_for_model,
            },
        }
        if self.generations > 1:
            payload["parameters"]["do_sample"] = True

        req_response = requests.request(
            "POST", self.api_url, headers=self.headers, data=json.dumps(payload)
        )

        if req_response.status_code == 503:
            self.wait_for_model = True
            raise HFLoadingException

        if (
            self.wait_for_model
        ):  # if we get this far, reset the model load wait. let's hope 503 is only for model loading :|
            self.wait_for_model = False

        response = json.loads(req_response.content.decode("utf-8"))
        if isinstance(response, dict):
            if "error" in response.keys():
                if isinstance(response["error"], list) and isinstance(
                    response["error"][0], str
                ):
                    logging.error(
                        f"Received list of errors, processing first only. Response: {response['error']}"
                    )
                    response["error"] = response["error"][0]
                if "rate limit" in response["error"].lower():
                    raise HFRateLimitException(response["error"])
                else:
                    raise IOError("🤗 " + response["error"])
            else:
                raise TypeError(
                    f"Unsure how to parse 🤗 API response dict: {response}, please open an issue at https://github.com/leondz/garak/issues including this message"
                )
        elif isinstance(response, list):
            return [g["generated_text"] for g in response]
        else:
            raise TypeError(
                f"Unsure how to parse 🤗 API response type: {response}, please open an issue at https://github.com/leondz/garak/issues including this message"
            )

    def generate(self, prompt):
        return self._call_api(prompt)


default_class = "Local"
