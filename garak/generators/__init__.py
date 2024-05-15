# generators/__init__.py

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from logging import getLogger
import importlib
from garak.generators.base import Generator

logger = getLogger(__name__)


def load_generator(
    model_name: str, model_type: str, generations: int = 10
) -> Generator:
    if (
        model_type in ("openai", "replicate", "ggml", "huggingface", "litellm")
        and not model_name
    ):
        message = f"⚠️  Model type '{model_type}' also needs a model name"
        logger.error(message)
        raise ValueError(message)
    generator_module_name = model_type.split(".")[0]
    generator_mod = importlib.import_module("garak.generators." + generator_module_name)
    if "." not in model_type:
        if generator_mod.DEFAULT_CLASS:
            generator_class_name = generator_mod.DEFAULT_CLASS
        else:
            raise Exception(
                "module {generator_module_name} has no default class; pass module.ClassName to model_type"
            )
    else:
        generator_class_name = model_type.split(".")[1]

    if not model_name:
        generator = getattr(generator_mod, generator_class_name)()
    else:
        generator = getattr(generator_mod, generator_class_name)(model_name)
    generator.generations = generations

    return generator
