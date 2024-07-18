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

import inspect
import logging
import os
import re
from typing import Callable, List, Union
import warnings

import backoff
import torch
from PIL import Image
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration

from garak import _config
from garak.exception import ModelNameMissingError, GarakException
from garak.generators.base import Generator


models_to_deprefix = ["gpt2"]


class HFRateLimitException(GarakException):
    pass


class HFLoadingException(GarakException):
    pass


class HFInternalServerError(GarakException):
    pass


class HFCompatible:
    def _set_hf_context_len(self, config):
        if hasattr(config, "n_ctx"):
            if isinstance(config.n_ctx, int):
                self.context_len = config.n_ctx

    def _gather_hf_params(self, hf_constructor: Callable):
        # this may be a bit too naive as it will pass any parameter valid for the pipeline signature
        # this falls over when passed `from_pretrained` methods as the callable model params are not explicit
        params = self.hf_args
        if params["device"] is None:
            params["device"] = self.device

        args = {}

        params_to_process = inspect.signature(hf_constructor).parameters

        if "model" in params_to_process:
            args["model"] = self.name
            # expand for
            params_to_process = {"do_sample": True} | params_to_process
        else:
            # callable is for a Pretrained class also map standard `pipeline` params
            from transformers import pipeline

            params_to_process = (
                {"low_cpu_mem_usage": True}
                | params_to_process
                | inspect.signature(pipeline).parameters
            )

        for k in params_to_process:
            if k == "model":
                continue  # special case `model` comes from `name` in the generator
            if k in params:
                val = params[k]
                if k == "torch_dtype" and hasattr(torch, val):
                    args[k] = getattr(
                        torch, val
                    )  # some model type specific classes do not yet support direct string representation
                    continue
                if (
                    k == "device"
                    and "device_map" in params_to_process
                    and "device_map" in params
                ):
                    # per transformers convention hold `device_map` before `device`
                    continue
                args[k] = params[k]

        return args

    def _select_hf_device(self):
        """Determine the most efficient device for tensor load, hold any existing `device` already selected"""
        import torch.cuda

        selected_device = None
        if self.hf_args.get("device", None) is not None:
            if isinstance(self.hf_args["device"], int):
                # this assumes that indexed only devices selections means `cuda`
                if self.hf_args["device"] < 0:
                    msg = f"device {self.hf_args['device']} requested but CUDA device numbering starts at zero. Use 'device: cpu' to request CPU."
                    logging.critical(msg)
                    raise ValueError(msg)
                selected_device = torch.device("cuda:" + str(self.hf_args["device"]))
            else:
                selected_device = torch.device(self.hf_args["device"])

        if selected_device is None:
            selected_device = torch.device(
                "cuda"
                if torch.cuda.is_available()
                else "mps" if torch.backends.mps.is_available() else "cpu"
            )

        if isinstance(selected_device, torch.device) and selected_device.type == "mps":
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            logging.debug("Enabled MPS fallback environment variable")

        logging.debug(
            "Using %s, based on torch environment evaluation", selected_device
        )
        return selected_device


class Pipeline(Generator, HFCompatible):
    """Get text generations from a locally-run Hugging Face pipeline"""

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "generations": 10,
        "hf_args": {
            "torch_dtype": "float16",
            "do_sample": True,
            "device": None,
        },
    }
    generator_family_name = "Hugging Face 🤗 pipeline"
    supports_multiple_generations = True
    parallel_capable = False

    def __init__(self, name="", config_root=_config):
        self.name = name

        super().__init__(self.name, config_root=config_root)

        import torch.multiprocessing as mp

        mp.set_start_method("spawn", force=True)

        self.device = self._select_hf_device()
        self._load_client()

    def _load_client(self):
        if hasattr(self, "generator") and self.generator is not None:
            return

        from transformers import pipeline, set_seed

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        pipeline_kwargs = self._gather_hf_params(hf_constructor=pipeline)
        self.generator = pipeline("text-generation", **pipeline_kwargs)
        if not hasattr(self, "deprefix_prompt"):
            self.deprefix_prompt = self.name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

        self._set_hf_context_len(self.generator.model.config)

    def _clear_client(self):
        self.generator = None

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        self._load_client()
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
    doc_uri = "https://huggingface.co/blog/optimum-nvidia"

    def _load_client(self):
        if hasattr(self, "generator") and self.generator is not None:
            return

        try:
            from optimum.nvidia.pipelines import pipeline
            from transformers import set_seed
        except Exception as e:
            logging.exception(e)
            raise GarakException(
                f"Missing required dependencies for {self.__class__.__name__}"
            )

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        import torch.cuda

        if not torch.cuda.is_available():
            message = "OptimumPipeline needs CUDA, but torch.cuda.is_available() returned False; quitting"
            logging.critical(message)
            raise GarakException(message)

        self.use_fp8 = False
        if _config.loaded:
            if "use_fp8" in _config.plugins.generators.OptimumPipeline:
                self.use_fp8 = True

        pipline_kwargs = self._gather_hf_params(hf_constructor=pipeline)
        self.generator = pipeline("text-generation", **pipline_kwargs)
        if not hasattr(self, "deprefix_prompt"):
            self.deprefix_prompt = self.name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

        self._set_hf_context_len(self.generator.model.config)


class ConversationalPipeline(Pipeline, HFCompatible):
    """Conversational text generation using HuggingFace pipelines"""

    generator_family_name = "Hugging Face 🤗 pipeline for conversations"
    supports_multiple_generations = True

    def _load_client(self):
        if hasattr(self, "generator") and self.generator is not None:
            return

        from transformers import pipeline, set_seed, Conversation

        if _config.run.seed is not None:
            set_seed(_config.run.seed)

        # Note that with pipeline, in order to access the tokenizer, model, or device, you must get the attribute
        # directly from self.generator instead of from the ConversationalPipeline object itself.
        pipline_kwargs = self._gather_hf_params(hf_constructor=pipeline)
        self.generator = pipeline("conversational", **pipline_kwargs)
        self.conversation = Conversation()
        if not hasattr(self, "deprefix_prompt"):
            self.deprefix_prompt = self.name in models_to_deprefix
        if _config.loaded:
            if _config.run.deprefix is True:
                self.deprefix_prompt = True

        self._set_hf_context_len(self.generator.model.config)

    def clear_history(self):
        from transformers import Conversation

        self.conversation = Conversation()

    def _call_model(
        self, prompt: Union[str, List[dict]], generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        """Take a conversation as a list of dictionaries and feed it to the model"""

        self._load_client()
        # If conversation is provided as a list of dicts, create the conversation.
        # Otherwise, maintain state in Generator
        if isinstance(prompt, str):
            self.conversation.add_message({"role": "user", "content": prompt})
            self.conversation = self.generator(self.conversation)
            generations = [self.conversation[-1]["content"]]  # what is this doing?

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


class InferenceAPI(Generator):
    """Get text generations from Hugging Face Inference API"""

    generator_family_name = "Hugging Face 🤗 Inference API"
    supports_multiple_generations = True
    import requests

    ENV_VAR = "HF_INFERENCE_TOKEN"
    URI = "https://api-inference.huggingface.co/models/"
    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "deprefix_prompt": True,
        "max_time": 20,
        "wait_for_model": False,
    }

    def __init__(self, name="", generations=10, config_root=_config):
        self.name = name
        self.generations = generations
        super().__init__(
            self.name, generations=self.generations, config_root=config_root
        )

        self.uri = self.URI + name

        # special case for api token requirement this also reserves `headers` as not configurable
        if self.api_key:
            self.headers = {"Authorization": f"Bearer {self.api_key}"}
        else:
            self.headers = {}
            message = " ⚠️  No Hugging Face Inference API token in HF_INFERENCE_TOKEN, expect heavier rate-limiting"
            print(message)
            logging.info(message)

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
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
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
            self.uri,
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


class InferenceEndpoint(InferenceAPI):
    """Interface for Hugging Face private endpoints

    Pass the model URL as the name, e.g. https://xxx.aws.endpoints.huggingface.cloud
    """

    supports_multiple_generations = False
    import requests

    timeout = 120

    def __init__(self, name="", generations=10, config_root=_config):
        super().__init__(name, generations=generations, config_root=config_root)
        self.uri = name

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
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
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
            self.uri, headers=self.headers, json=payload, timeout=self.timeout
        ).json()
        try:
            output = response[0]["generated_text"]
        except Exception as exc:
            raise IOError(
                "Hugging Face 🤗 endpoint didn't generate a response. Make sure the endpoint is active."
            ) from exc
        return [output]


class Model(Pipeline, HFCompatible):
    """Get text generations from a locally-run Hugging Face model"""

    generator_family_name = "Hugging Face 🤗 model"
    supports_multiple_generations = True

    def _load_client(self):
        if hasattr(self, "model") and self.model is not None:
            return

        import transformers

        if _config.run.seed is not None:
            transformers.set_seed(_config.run.seed)

        trust_remote_code = self.name.startswith("mosaicml/mpt-")

        model_kwargs = self._gather_hf_params(
            hf_constructor=transformers.AutoConfig.from_pretrained
        )  # will defer to device_map if device map was `auto` may not match self.device

        self.config = transformers.AutoConfig.from_pretrained(
            self.name, trust_remote_code=trust_remote_code, **model_kwargs
        )

        self._set_hf_context_len(self.config)
        self.config.init_device = self.device  # determined by Pipeline `__init__``

        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            self.name, config=self.config
        ).to(self.device)

        if not hasattr(self, "deprefix_prompt"):
            self.deprefix_prompt = self.name in models_to_deprefix

        if self.config.tokenizer_class:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.config.tokenizer_class
            )
        else:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.name, padding_side="left"
            )

        self.generation_config = transformers.GenerationConfig.from_pretrained(
            self.name
        )
        self.generation_config.eos_token_id = self.model.config.eos_token_id
        self.generation_config.pad_token_id = self.model.config.eos_token_id

    def _clear_client(self):
        self.model = None
        self.config = None
        self.tokenizer = None
        self.generation_config = None

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        self._load_client()
        self.generation_config.max_new_tokens = self.max_tokens
        self.generation_config.do_sample = self.hf_args["do_sample"]
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
                ).to(self.device)

                try:
                    outputs = self.model.generate(
                        **inputs, generation_config=self.generation_config
                    )
                except Exception as e:
                    if len(prompt) == 0:
                        returnval = [None] * generations_this_call
                        logging.exception("Error calling generate for empty prompt")
                        print(returnval)
                        return returnval
                    else:
                        raise e
                text_output = self.tokenizer.batch_decode(
                    outputs, skip_special_tokens=True, device=self.device
                )

        if not self.deprefix_prompt:
            return text_output
        else:
            return [re.sub("^" + re.escape(prompt), "", i) for i in text_output]


class LLaVA(Generator, HFCompatible):
    """Get LLaVA ([ text + image ] -> text) generations"""

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "max_tokens": 4000,
        # "exist_tokens + max_new_tokens < 4K is the golden rule."
        # https://github.com/haotian-liu/LLaVA/issues/1095#:~:text=Conceptually%2C%20as%20long%20as%20the%20total%20tokens%20are%20within%204K%2C%20it%20would%20be%20fine%2C%20so%20exist_tokens%20%2B%20max_new_tokens%20%3C%204K%20is%20the%20golden%20rule.
        "hf_args": {
            "torch_dtype": "float16",
            "low_cpu_mem_usage": True,
            "device_map": "auto",
        },
    }

    # rewrite modality setting
    modality = {"in": {"text", "image"}, "out": {"text"}}
    parallel_capable = False

    # Support Image-Text-to-Text models
    # https://huggingface.co/llava-hf#:~:text=Llava-,Models,-9
    supported_models = [
        "llava-hf/llava-v1.6-34b-hf",
        "llava-hf/llava-v1.6-vicuna-13b-hf",
        "llava-hf/llava-v1.6-vicuna-7b-hf",
        "llava-hf/llava-v1.6-mistral-7b-hf",
    ]

    def __init__(self, name="", generations=10, config_root=_config):
        super().__init__(name, generations=generations, config_root=config_root)
        if self.name not in self.supported_models:
            raise ModelNameMissingError(
                f"Invalid model name {self.name}, current support: {self.supported_models}."
            )

        self.device = self._select_hf_device()
        model_kwargs = self._gather_hf_params(
            hf_constructor=LlavaNextForConditionalGeneration.from_pretrained
        )  # will defer to device_map if device map was `auto` may not match self.device

        self.processor = LlavaNextProcessor.from_pretrained(self.name)
        self.model = LlavaNextForConditionalGeneration.from_pretrained(
            self.name, **model_kwargs
        )

        self.model.to(self.device)

    def generate(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        text_prompt = prompt["text"]
        try:
            image_prompt = Image.open(prompt["image"])
        except FileNotFoundError:
            raise FileNotFoundError(f"Cannot open image {prompt['image']}.")
        except Exception as e:
            raise Exception(e)

        inputs = self.processor(text_prompt, image_prompt, return_tensors="pt").to(
            self.device
        )
        exist_token_number: int = inputs.data["input_ids"].shape[1]
        output = self.model.generate(
            **inputs, max_new_tokens=self.max_tokens - exist_token_number
        )
        output = self.processor.decode(output[0], skip_special_tokens=True)

        return [output]


DEFAULT_CLASS = "Pipeline"
