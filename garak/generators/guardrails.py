"""NeMo Guardrails generator."""

from typing import List

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
            raise Exception(
                "You must first install NeMo Guardrails using `pip install nemoguardrails`."
            ) from e

        self.name = name
        self.fullname = f"Guardrails {self.name}"

        # Currently, we use the model_name as the path to the config
        config = RailsConfig.from_path(self.name)
        self.rails = LLMRails(config=config)

        super().__init__(name, generations=generations)

    def _call_model(self, prompt: str) -> List[str]:
        # print(f"{prompt}")

        result = self.rails.generate(prompt)
        # print(result)
        # print(repr(result))
        # print("--")

        return result


default_class = "NeMoGuardrails"
