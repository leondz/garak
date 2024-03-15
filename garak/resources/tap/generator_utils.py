# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import tiktoken
from typing import Union

from garak.generators.openai import chat_models, OpenAIGenerator
from garak.generators.huggingface import Model

supported_openai = chat_models
supported_huggingface = [
    "lmsys/vicuna-13b-v1.3",
    "lmsys/vicuna-7b-v1.3"
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
    if model_name.lower() in hf_dict.keys():
        model_name = hf_dict[model_name]

    if model_name in supported_openai:
        generator = OpenAIGenerator(
            model_name,
            generations=generations,
        )
    elif model_name in supported_huggingface:
        generator = Model(model_name, generations=generations, device=device)
    else:
        msg = (
            f"{model_name} is not currently supported for TAP generation. Support is available for the following "
            f"OpenAI and HuggingFace models:\nOpenAI: {supported_openai}\nHuggingFace: {supported_huggingface}\n"
            f"Your jailbreaks will *NOT* be saved."
        )
        print(msg)
        generator = Model(model_name, generations=generations, device=device)

    generator.max_tokens = max_tokens
    if temperature is not None:
        generator.temperature = temperature

    return generator


def token_count(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_token_limit(model_name: str) -> int:
    match model_name:
        case "gpt-3.5-turbo":
            return 16385
        case "gpt-4":
            return 8192
        case "gpt-4-32k":
            return 32768
        case "gpt-4-turbo-preview":
            return 128000
        case _:
            # Base case, return smallest context
            return 4096
