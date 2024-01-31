# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import List

import openai
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


def load_generator(model_name: str, generations: int = 1, max_tokens: int = 150, temperature: float = None):
    if model_name.lower() in hf_dict.keys():
        model_name = hf_dict[model_name]

    if model_name in supported_openai:
        generator = OpenAIConvGenerator(model_name, max_tokens=max_tokens, temperature=temperature,
                                        generations=generations)
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


class OpenAIConvGenerator(OpenAIGenerator):
    def __init__(self, model_name, max_tokens: int = 150, temperature: float = 0.0, generations=1):
        super().__init__(model_name, generations=generations)

        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, prompts: list) -> list[str]:
        response = self.generator.create(
            model=self.name,
            messages=prompts,
            temperature=self.temperature,
            top_p=self.top_p,
            n=self.generations,
            stop=self.stop,
            max_tokens=self.max_tokens,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
        )
        return [c["message"]["content"] for c in response["choices"]]
