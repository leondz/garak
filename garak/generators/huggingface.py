#!/usr/bin/env python3
"""Hugging Face generator

Supports pipelines, inference API, and models.

Not all models on HF Hub work well with pipelines; try a Model generator
if there are problems. Otherwise, please let us know if it's still not working!

 https://github.com/leondz/garak/issues

If you use the inference API, it's recommended to put your Hugging Face API key
in an environment variable called HF_INFERENCE_TOKEN , else the rate limiting can
be quite strong. Find your Hugging Face Inference API Key here:

 https://huggingface.co/docs/api-inference/quicktour
"""

import logging
import re
import os
from typing import List
import warnings

import backoff

from garak._config import args
from garak.generators.base import Generator


models_to_deprefix = ["gpt2"]


class HFRateLimitException(Exception):
    pass


class HFLoadingException(Exception):
    pass


class HFInternalServerError(Exception):
    pass


class Pipeline(Generator):
    generator_family_name = "Hugging Face 🤗 pipeline"

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        super().__init__(name, generations=generations)

        from transformers import pipeline, set_seed

        if "seed" in dir(args):
            set_seed(args.seed)

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

    def generate(self, prompt):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            try:
                # workaround for pipeline to truncate the input
                encoded_prompt = self.generator.tokenizer(prompt, truncation=True)
                truncated_prompt = self.generator.tokenizer.decode(
                    encoded_prompt["input_ids"], skip_special_tokens=True
                )
                raw_output = self.generator(
                    truncated_prompt,
                    pad_token_id=self.generator.tokenizer.eos_token_id,
                    max_new_tokens=self.max_tokens,
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
    generator_family_name = "Hugging Face 🤗 Inference API"

    def __init__(self, name="", generations=10):
        self.api_url = "https://api-inference.huggingface.co/models/" + name
        self.api_token = os.getenv("HF_INFERENCE_TOKEN", default=None)
        self.fullname, self.name = name, name
        super().__init__(name, generations=generations)

        if self.api_token:
            self.headers = {"Authorization": f"Bearer {self.api_token}"}
        else:
            self.headers = {}
            message = " ⚠️  No Hugging Face Inference API token in HF_INFERENCE_TOKEN, expect heavier rate-limiting"
            print(message)
            logging.info(message)
        self.deprefix_prompt = True
        self.max_time = 20

    @backoff.on_exception(
        backoff.fibo,
        (HFRateLimitException, HFLoadingException, HFInternalServerError),
        max_value=125,
    )
    def _call_api(self, prompt: str) -> List[str]:
        import json
        import requests

        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": not self.deprefix_prompt,
                "num_return_sequences": self.generations,
                "max_time": self.max_time,
            },
            "options": {
                "wait_for_model": self.wait_for_model,
            },
        }
        if self.max_tokens:
            payload["parameters"]["max_new_tokens"] = self.max_tokens

        if self.generations > 1:
            payload["parameters"]["do_sample"] = True

        req_response = requests.request(
            "POST", self.api_url, headers=self.headers, data=json.dumps(payload)
        )

        if req_response.status_code == 503:
            self.wait_for_model = True
            raise HFLoadingException

        # if we get this far, reset the model load wait. let's hope 503 is only for model loading :|
        if self.wait_for_model:
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
                    if req_response.status_code == 500:
                        raise HFInternalServerError()
                    else:
                        raise IOError(
                            f"🤗 reported: {req_response.status_code} "
                            + response["error"]
                        )
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
        self.wait_for_model = False
        return self._call_api(prompt)


class Model(Pipeline):
    generator_family_name = "Hugging Face 🤗 model"

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        super(Pipeline, self).__init__(name, generations=generations)

        import transformers

        if "seed" in dir(args):
            transformers.set_seed(args.seed)

        init_device = "meta"
        import torch.cuda

        if torch.cuda.is_available() == False:
            logging.debug("Using CPU, torch.cuda.is_available() returned False")
            device = -1
            init_device = "cpu"

        trust_remote_code = self.fullname.startswith("mosaicml/mpt-")

        self.config = transformers.AutoConfig.from_pretrained(
            self.fullname, trust_remote_code=trust_remote_code
        )
        self.config.init_device = (
            init_device  # or "cuda:0" For fast initialization directly on GPU!
        )

        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            self.fullname,
            trust_remote_code=trust_remote_code,
            config=self.config,
        )
        self.deprefix_prompt = name in models_to_deprefix

        if self.config.tokenizer_class:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.config.tokenizer_class
            )
        else:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.fullname, padding_side="left"
            )

        self.generator = transformers.pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            do_sample=do_sample,
            device=device,
        )
        self.deprefix_prompt = self.fullname in models_to_deprefix


default_class = "Pipeline"
