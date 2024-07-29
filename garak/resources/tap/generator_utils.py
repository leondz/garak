# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import tiktoken
from typing import Union

from garak.generators.openai import chat_models, context_lengths, OpenAIGenerator
from garak.generators.huggingface import Model

supported_openai = chat_models
supported_huggingface = [
    "lmsys/vicuna-13b-v1.3",
    "lmsys/vicuna-7b-v1.3",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "meta-llama/Llama-2-7b-chat-hf",
]
hf_dict = {
    "vicuna": "lmsys/vicuna-13b-v1.3",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
}


def load_generator(
    model_name: str,
    generations: int = 1,
    max_tokens: int = 150,
    temperature: float = None,
    device: Union[int, str] = 0,
):
    """
    Function to load a generator

    Parameters
    ----------
    model_name : Name of the model to load
    generations : Number of outputs to generate per call
    max_tokens : Maximum output tokens
    temperature : Model temperature
    device : Device to run the model on. Accepts GPU ID (int) or "cpu"

    Returns
    -------
    Generator object

    """

    config = {
        "name": model_name,
        "generations": generations,
        "max_tokens": max_tokens,
    }

    if temperature is not None:
        config["temperature"] = temperature

    if model_name.lower() in hf_dict.keys():
        config["name"] = hf_dict[model_name]

    if model_name in supported_openai:
        config_root = {
            "generators": {
                OpenAIGenerator.__module__.split(".")[-1]: {
                    OpenAIGenerator.__name__: config
                }
            }
        }
        generator = OpenAIGenerator(config_root=config_root)
    elif model_name in supported_huggingface:
        config["hf_args"] = {"device": device}
        config_root = {
            "generators": {Model.__module__.split(".")[-1]: {Model.__name__: config}}
        }
        generator = Model(config_root=config_root)
    else:
        msg = (
            f"{model_name} is not currently supported for TAP generation. Support is available for the following "
            f"OpenAI and HuggingFace models:\nOpenAI: {supported_openai}\nHuggingFace: {supported_huggingface}\n"
            f"Your jailbreaks will *NOT* be saved."
        )
        print(msg)
        generator = Model(config_root=config)

    return generator


def token_count(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_token_limit(model_name: str) -> int:
    if model_name in context_lengths:
        return context_lengths[model_name]
    else:
        return 4096
