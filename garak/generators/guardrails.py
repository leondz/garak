# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NeMo Guardrails generator."""

from contextlib import redirect_stderr
import io
from typing import List, Union

from garak.generators.base import Generator


class NeMoGuardrails(Generator):
    """Generator wrapper for NeMo Guardrails."""

    supports_multiple_generations = False
    generator_family_name = "Guardrails"

    def __init__(self, name, generations=1):
        try:
            from nemoguardrails import RailsConfig, LLMRails
            from nemoguardrails.logging.verbose import set_verbose
        except ImportError as e:
            raise NameError(
                "You must first install NeMo Guardrails using `pip install nemoguardrails`."
            ) from e

        self.name = name
        self.fullname = f"Guardrails {self.name}"

        # Currently, we use the model_name as the path to the config
        with redirect_stderr(io.StringIO()) as f:  # quieten the tqdm
            config = RailsConfig.from_path(self.name)
            self.rails = LLMRails(config=config)

        super().__init__(name, generations=generations)

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> Union[List[str], str, None]:
        with redirect_stderr(io.StringIO()) as f:  # quieten the tqdm
            result = self.rails.generate(prompt)

        return result


default_class = "NeMoGuardrails"
