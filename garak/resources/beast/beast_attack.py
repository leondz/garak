# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Union, Optional

import torch
import numpy as np
import pandas as pd

import garak._config
from garak.generators import Generator
from garak.resources.common import rejection_strings, advbench_path

beast_resource_data = garak._config.transient.basedir / "resources" / "beast" / "data"


def format_chat(prompt: str):
    # TODO: Implement this functionality!
    return prompt


@torch.no_grad()
def evaluate(generator, prompt, best_candidate):
    result = False
    best_candidate_str = generator.tokenizer.decode(best_candidate)
    input_str = prompt + best_candidate_str
    outputs = generator.generate(input_str)
    results = check_jailbreak(outputs)
    if all(results):
        result = True
    return result, outputs[0]


@torch.no_grad()
def evaluate_target(generator, prompt, best_candidate, target):
    result = False
    best_candidate_str = generator.tokenizer.decode(best_candidate)
    input_str = prompt + best_candidate_str
    outputs = generator.generate(input_str)
    for output in outputs:
        if target in output:
            result = True
            return result, output
    return result, outputs[0]


def tensorize(generator: Generator,
              prompt: str,
              response: str,
              suffix_ids: Union[list[int], torch.Tensor, None] = None) -> tuple[torch.Tensor, int]:
    """
    Turn prompt and response into tensors of tokens
    Args:
        generator: targeted generator
        prompt: prompt to the model
        response: response from the model
        suffix_ids: suffix_ids, if any.
    Returns:
        encoding_tensor: Tensor of tokenized inputs
        split: Index of tensor where model output begins
    """
    suffix_tensor = torch.tensor([], dtype=torch.long)
    if suffix_ids is not None:
        suffix_tensor = torch.tensor(suffix_ids, dtype=torch.long) if isinstance(suffix_ids, list) else suffix_ids
    prompt_encoding = generator.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").squeeze(0)
    output_encoding = generator.tokenizer.encode(response, add_special_tokens=False, return_tensors="pt").squeeze(0)
    encoding_tensor = torch.cat((prompt_encoding, suffix_tensor, output_encoding))
    split = encoding_tensor.shape[0] - output_encoding.shape[0]

    return encoding_tensor, split


@torch.no_grad()
def get_perplexity(generator: Generator,
                   prompt: str,
                   response: str,
                   suffix_ids: Union[list[int], torch.Tensor, None] = None) -> float:
    """
    Given a generator and a prompt, returns the perplexity of the input.
    Args:
        generator: targeted generator
        prompt: prompt to the model
        response: response from the model
        suffix_ids: suffix_ids, if any.

    Returns:
        perplexity: float value for the perplexity of the prompt.
    """
    encoding_tensor, split = tensorize(generator, prompt, response, suffix_ids)
    input_tensor = encoding_tensor.unsqueeze(0).to(generator.model.device)

    logits = generator.model(input_tensor).logits
    output_logits = logits[:, split - 1:, :]
    logprobs = torch.nn.functional.log_softmax(output_logits, dim=-1)

    # Calculate perplexity
    gather_index = input_tensor[:, split:].unsqueeze(-1)
    gathered_logprobs = logprobs.gather(2, gather_index)
    mean_logprobs = gathered_logprobs.mean(dim=1)
    perplexity = torch.exp(-mean_logprobs).item()

    return perplexity


def check_jailbreak(outputs: list[str]) -> list[int]:
    """
    Check list of outputs for rejection, assuming no rejection is a success.
    Args:
        outputs: List of output strings
    Returns:
        acc: List of boolean -- 1 for not rejected, 0 for rejected.
    """
    acc = [0 for _ in range(len(outputs))]
    for idx, output in enumerate(outputs):
        if not any([rs in output for rs in rejection_strings]):
            acc[idx] = 1
    return acc


@torch.no_grad()
def sample_tokens(generator: Generator,
                  prompt: str,
                  response: str,
                  k: int,
                  suffix_ids: Union[list[int], torch.Tensor, None] = None) -> list[int]:
    """
    Sample the generator for a new response
    Args:
        generator: targeted generator
        prompt: prompt to the model
        response: response from the model
        k: number of samples
        suffix_ids: suffix_ids, if any.
    Returns:
        tokens: List of tokens
    """
    tensor, split = tensorize(generator, prompt, response, suffix_ids)
    tensor = tensor[:split].unsqueeze(0).to(generator.model.device)
    logits = generator.model(tensor).logits[:, -1, :]
    probs = torch.softmax(logits / generator.temperature, dim=-1)
    tokens = torch.multinomial(probs, k, replacement=False)
    return tokens[0].tolist()


@torch.no_grad()
def get_best_candidate(generator: Generator,
                       prompt: str,
                       response: str,
                       k1: int,
                       k2: int,
                       suffix_len: int,
                       suffix_ids: Union[list[int], torch.Tensor, None] = None) -> tuple[list[int], float]:
    """
    Return the best candidate suffix and its associated score.

    Args:
        generator ():
        prompt ():
        response ():
        k1 ():
        k2 ():
        suffix_len ():
        suffix_ids ():

    Returns:
        best_suffix: The best performing adversarial suffix
        best_score: The best score
    """
    best_suffix = ""
    best_score = np.Inf

    beams = [[sample] for sample in sample_tokens(generator, prompt, response, k1, suffix_ids)]
    for i in range(1, suffix_len):
        candidates = list()
        for beam in beams:
            for next_token in sample_tokens(generator, prompt, response, k2, beam):
                candidates.append(beam + [next_token])

        scores = [get_perplexity(generator, prompt, response, candidate) for candidate in candidates]
        sorted_scores = sorted(range(len(scores)), key=lambda i: scores[i])
        beams = [candidates[i] for i in sorted_scores[:k1]]

        best_candidate = candidates[sorted_scores[0]]
        candidate_score = scores[sorted_scores[i]]

        if candidate_score < best_score:
            best_score = candidate_score
            best_suffix = best_candidate

    return best_suffix, best_score


def attack(generator: Generator,
           prompts: list[str],
           k1: int = 15,
           k2: int = 15,
           trials: int = 1,
           suffix_len: int = 40,
           target: Optional[str] = "") -> list[str]:
    """

    Args:
        generator: target generator to attack
        prompts: Input prompt
        k1: Number of candidates in beam
        k2: Number of candidates to evaluate
        trials: Number of generations to run for the attack
        suffix_len: Number of adversarial tokens to generate
        targeted: Target phrase (only for targeted attack!)
        target: Target output string

    Returns:
        prompt_tokens: Adversarial prompt tokens
        scores: Score for attack objective per item in prompt_tokens
    """
    suffixes = list()
    prompts = [format_chat(prompt) for prompt in prompts]
    response = ""

    for prompt in prompts:
        best_candidate = []
        for _ in range(trials):
            best_candidate, score = get_best_candidate(generator, prompt, response, k1, k2, suffix_len, best_candidate)

        if target:
            result, response = evaluate_target(generator, prompt, best_candidate, target)
        else:
            result, response = evaluate(generator, prompt, best_candidate)

        if result:
            suffixes.append(generator.tokenizer.decode(best_candidate))

    return suffixes


def run_beast(
    target_generator: garak.generators.Generator = None,
    prompts: Optional[list[str]] = None,
    k1: int = 15,
    k2: int = 15,
    trials: int = 1,
    suffix_len: int = 40,
    target: Optional[str] = "",
    outfile: str = beast_resource_data / "suffixes.txt",
) -> Union[list[str], None]:
    """
    Function to run BEAST attack
    Args:
        target_generator (Generator): Generator to target with attack
        prompts (list[str]): List of prompts (optional)
        k1 (int): Number of candidates in beam
        k2 (int): Number of candidates per candidate evaluated
        trials (int): Number of trial generations for attack
        suffix_len (int): Maximum number of adversarial tokens to generate
        target (str): Target output phrase (optional)
        outfile (str): Path to write generated suffixes

    Returns:
        suffixes (list[str]): List of adversarial suffixes as strings

    """
    if not hasattr(target_generator, "model") or not hasattr(target_generator, "tokenizer"):
        raise ValueError(f"{target_generator.name} does not have both a `model` and `tokenizer` attribute. "
                         f"Cannot run BEAST.")

    if not prompts:
        data = pd.read_csv(advbench_path)
        prompts = data["target"].tolist()

    suffixes = attack(generator=target_generator,
                      prompts=prompts,
                      k1=k1,
                      k2=k2,
                      trials=trials,
                      suffix_len=suffix_len,
                      target=target)

    if suffixes:
        with open(outfile, "a") as f:
            for suffix in suffixes:
                f.write(f"{suffix}\n")
        return suffixes
    else:
        return None
