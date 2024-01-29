# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import torch

from garak.generators.openai import chat_models, OpenAIGenerator
from garak.generators.huggingface import Model

supported_openai = chat_models
supported_huggingface = ["lmsys/vicuna-13b-v1.3",
                         "mistralai/Mistral-7B-Instruct-v0.2",
                         "meta-llama/Llama-2-7b-chat-hf"]
hf_dict = {"vicuna": "lmsys/vicuna-13b-v1.3",
           "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
           "llama2": "meta-llama/Llama-2-7b-chat-hf"}
device = 0 if torch.cuda.is_available() else "cpu"


def load_generator(model_name: str, generations: int = 5, max_tokens: int = 150, temperature: float = None):
    if model_name.lower() in hf_dict.keys():
        model_name = hf_dict[model_name]

    if model_name in supported_openai:
        generator = OpenAIGenerator(model_name, generations=generations)
        generator.max_tokens = max_tokens
        if temperature is not None:
            generator.temperature = temperature
    elif model_name in supported_huggingface:
        generator = Model(model_name, generations=generations, device=device)
        generator.max_tokens = max_tokens
        if temperature is not None:
            generator.temperature = temperature
    else:
        msg = (f"I'm sorry, that model is not currently supported. TAP generation supports the following models:"
               f"\nOpenAI: {supported_openai}\nHuggingFace: {supported_huggingface}")
        raise Exception(msg)

    return generator

