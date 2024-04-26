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
from math import log
import re
import os
from typing import List, Union
import warnings

import backoff
import torch

from garak import _config
from garak.generators.base import Generator


models_to_deprefix = ["gpt2"]


class HFRateLimitException(Exception):
    pass


class HFLoadingException(Exception):
    pass


class HFInternalServerError(Exception):
    pass


class HFCompatible:
    def _set_hf_context_len(self, config):
        if hasattr(config, "n_ctx"):
            if isinstance(config.n_ctx, int):
                self.context_len = config.n_ctx


class Pipeline(Generator, HFCompatible):
    """Get text generations from a locally-run Hugging Face pipeline"""

    generator_family_name = "Hugging Face 🤗 pipeline"
    supports_multiple_generations = True

    def _set_hf_context_len(self, config):
        if hasattr(config, "n_ctx"):
            if isinstance(config.n_ctx, int):
                self.context_len = config.n_ctx

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        super().__init__(name, generations=generations)

        from transformers import pipeline, set_seed

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        import torch.cuda

        if not torch.cuda.is_available():
            logging.debug("Using CPU, torch.cuda.is_available() returned False")
            device = -1

        self.generator = pipeline(
            "text-generation",
            model=name,
            do_sample=do_sample,
            device=device,
        )
        self.deprefix_prompt = name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

                self._set_hf_context_len(self.generator.model.config)

    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[str]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            try:
                with torch.no_grad():
                    # workaround for pipeline to truncate the input
                    encoded_prompt = self.generator.tokenizer(prompt, truncation=True)
                    truncated_prompt = self.generator.tokenizer.decode(
                        encoded_prompt["input_ids"], skip_special_tokens=True
                    )
                    raw_output = self.generator(
                        truncated_prompt,
                        pad_token_id=self.generator.tokenizer.eos_token_id,
                        max_new_tokens=self.max_tokens,
                        num_return_sequences=generations_this_call,
                    )
            except Exception as e:
                logging.error(e)
                raw_output = []  # could handle better than this

        outputs = []
        if raw_output is not None:
            outputs = [
                i["generated_text"] for i in raw_output
            ]  # generator returns 10 outputs by default in __init__

        if not self.deprefix_prompt:
            return outputs
        else:
            return [re.sub("^" + re.escape(prompt), "", _o) for _o in outputs]


class OptimumPipeline(Pipeline, HFCompatible):
    """Get text generations from a locally-run Hugging Face pipeline using NVIDIA Optimum"""

    generator_family_name = "NVIDIA Optimum Hugging Face 🤗 pipeline"
    supports_multiple_generations = True
    uri = "https://huggingface.co/blog/optimum-nvidia"

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        super().__init__(name, generations=generations)

        from optimum.nvidia.pipelines import pipeline
        from transformers import set_seed

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        import torch.cuda

        if not torch.cuda.is_available():
            message = "OptimumPipeline needs CUDA, but torch.cuda.is_available() returned False; quitting"
            logging.critical(message)
            raise ValueError(message)

        use_fp8 = False
        if _config.loaded:
            if "use_fp8" in _config.plugins.generators.OptimumPipeline:
                use_fp8 = True

        self.generator = pipeline(
            "text-generation",
            model=name,
            do_sample=do_sample,
            device=device,
            use_fp8=use_fp8,
        )
        self.deprefix_prompt = name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

        self._set_hf_context_len(self.generator.model.config)


class ConversationalPipeline(Generator, HFCompatible):
    """Conversational text generation using HuggingFace pipelines"""

    generator_family_name = "Hugging Face 🤗 pipeline for conversations"
    supports_multiple_generations = True

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]

        super().__init__(name, generations=generations)

        from transformers import pipeline, set_seed, Conversation

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        import torch.cuda

        if not torch.cuda.is_available():
            logging.debug("Using CPU, torch.cuda.is_available() returned False")
            device = -1

        # Note that with pipeline, in order to access the tokenizer, model, or device, you must get the attribute
        # directly from self.generator instead of from the ConversationalPipeline object itself.
        self.generator = pipeline(
            "conversational",
            model=name,
            do_sample=do_sample,
            device=device,
        )
        self.conversation = Conversation()
        self.deprefix_prompt = name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

        self._set_hf_context_len(self.generator.model.config)

    def clear_history(self):
        from transformers import Conversation

        self.conversation = Conversation()

    def _call_model(
        self, prompt: Union[str, list[dict]], generations_this_call: int = 1
    ) -> List[str]:
        """Take a conversation as a list of dictionaries and feed it to the model"""

        # If conversation is provided as a list of dicts, create the conversation.
        # Otherwise, maintain state in Generator
        if isinstance(prompt, str):
            self.conversation.add_message({"role": "user", "content": prompt})
            self.conversation = self.generator(self.conversation)
            generations = [self.conversation[-1]["content"]]

        elif isinstance(prompt, list):
            from transformers import Conversation

            conversation = Conversation()
            for item in prompt:
                conversation.add_message(item)
            with torch.no_grad():
                conversation = self.generator(conversation)

            outputs = [conversation[-1]["content"]]
        else:
            raise TypeError(f"Expected list or str, got {type(prompt)}")

        if not self.deprefix_prompt:
            return outputs
        else:
            return [re.sub("^" + re.escape(prompt), "", _o) for _o in outputs]


class InferenceAPI(Generator, HFCompatible):
    """Get text generations from Hugging Face Inference API"""

    generator_family_name = "Hugging Face 🤗 Inference API"
    supports_multiple_generations = True
    import requests

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
        self.wait_for_model = False

    @backoff.on_exception(
        backoff.fibo,
        (
            HFRateLimitException,
            HFLoadingException,
            HFInternalServerError,
            requests.Timeout,
            TimeoutError,
        ),
        max_value=125,
    )
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[str]:
        import json
        import requests

        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": not self.deprefix_prompt,
                "num_return_sequences": generations_this_call,
                "max_time": self.max_time,
            },
            "options": {
                "wait_for_model": self.wait_for_model,
            },
        }
        if self.max_tokens:
            payload["parameters"]["max_new_tokens"] = self.max_tokens

        if generations_this_call > 1:
            payload["parameters"]["do_sample"] = True

        req_response = requests.request(
            "POST",
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=(20, 90),  # (connect, read)
        )

        if req_response.status_code == 503:
            self.wait_for_model = True
            raise HFLoadingException

        # if we get this far, reset the model load wait. let's hope 503 is only for model loading :|
        if self.wait_for_model:
            self.wait_for_model = False

        response = None
        try:
            response = json.loads(req_response.content.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            logging.error(
                "HF Inference API returned non-JSON: %s", req_response.content
            )
            response = req_response.content

        if isinstance(response, dict):
            if "error" in response.keys():
                if isinstance(response["error"], list) and isinstance(
                    response["error"][0], str
                ):
                    logging.error(
                        "Received list of errors, processing first only. Response: %s",
                        response["error"],
                    )
                    response["error"] = response["error"][0]

                if "rate limit" in response["error"].lower():
                    raise HFRateLimitException(response["error"])
                else:
                    if req_response.status_code == 500:
                        raise HFInternalServerError()
                    elif req_response.status_code == 504:
                        raise TimeoutError()
                    else:
                        raise IOError(
                            f"🤗 reported: {req_response.status_code} {response['error']}"
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

    def _pre_generate_hook(self):
        self.wait_for_model = False


class InferenceEndpoint(InferenceAPI, HFCompatible):
    """Interface for Hugging Face private endpoints
    Pass the model URL as the name, e.g. https://xxx.aws.endpoints.huggingface.cloud
    """

    supports_multiple_generations = False
    import requests

    timeout = 120

    def __init__(self, name="", generations=10):
        super().__init__(name, generations=generations)
        self.api_url = name

    @backoff.on_exception(
        backoff.fibo,
        (
            HFRateLimitException,
            HFLoadingException,
            HFInternalServerError,
            requests.Timeout,
        ),
        max_value=125,
    )
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[str]:
        import requests

        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": not self.deprefix_prompt,
                "max_time": self.max_time,
            },
            "options": {
                "wait_for_model": self.wait_for_model,
            },
        }
        if self.max_tokens:
            payload["parameters"]["max_new_tokens"] = self.max_tokens

        if generations_this_call > 1:
            payload["parameters"]["do_sample"] = True

        response = requests.post(
            self.api_url, headers=self.headers, json=payload, timeout=self.timeout
        ).json()
        try:
            output = response[0]["generated_text"]
        except Exception as exc:
            raise IOError(
                "Hugging Face 🤗 endpoint didn't generate a response. Make sure the endpoint is active."
            ) from exc
        return output


class Model(Generator, HFCompatible):
    """Get text generations from a locally-run Hugging Face model"""

    generator_family_name = "Hugging Face 🤗 model"
    supports_multiple_generations = True

    def __init__(self, name, do_sample=True, generations=10, device=0):
        self.fullname, self.name = name, name.split("/")[-1]
        self.device = device

        super().__init__(name, generations=generations)

        import transformers

        if _config.run.seed is not None:
            transformers.set_seed(_config.run.seed)

        self.init_device = "cuda:" + str(self.device)
        import torch.cuda

        if not torch.cuda.is_available():
            logging.debug("Using CPU, torch.cuda.is_available() returned False")
            self.device = -1
            self.init_device = "cpu"

        trust_remote_code = self.fullname.startswith("mosaicml/mpt-")

        self.config = transformers.AutoConfig.from_pretrained(
            self.fullname, trust_remote_code=trust_remote_code
        )
        self.config.init_device = (
            self.init_device  # or "cuda:0" For fast initialization directly on GPU!
        )

        self._set_hf_context_len(self.config)

        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            self.fullname,
            config=self.config,
        ).to(self.init_device)

        self.deprefix_prompt = name in models_to_deprefix

        if self.config.tokenizer_class:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.config.tokenizer_class
            )
        else:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.fullname, padding_side="left"
            )

        self.deprefix_prompt = self.fullname in models_to_deprefix
        self.do_sample = do_sample
        self.generation_config = transformers.GenerationConfig.from_pretrained(
            self.fullname
        )
        self.generation_config.eos_token_id = self.model.config.eos_token_id
        self.generation_config.pad_token_id = self.model.config.eos_token_id

    def _call_model(self, prompt: str, generations_this_call: int = 1):
        self.generation_config.max_new_tokens = self.max_tokens
        self.generation_config.do_sample = self.do_sample
        self.generation_config.num_return_sequences = generations_this_call
        if self.temperature is not None:
            self.generation_config.temperature = self.temperature
        if self.top_k is not None:
            self.generation_config.top_k = self.top_k

        text_output = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            with torch.no_grad():
                inputs = self.tokenizer(
                    prompt, truncation=True, return_tensors="pt"
                ).to(self.init_device)

                try:
                    outputs = self.model.generate(
                        **inputs, generation_config=self.generation_config
                    )
                except IndexError as e:
                    if len(prompt) == 0:
                        return [""] * generations_this_call
                    else:
                        raise e
                text_output = self.tokenizer.batch_decode(
                    outputs, skip_special_tokens=True, device=self.device
                )

        if not self.deprefix_prompt:
            return text_output
        else:
            return [re.sub("^" + re.escape(prompt), "", i) for i in text_output]


default_class = "Pipeline"
