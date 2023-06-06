import pandas as pd

from ._utils import hash_str
from .prompt_data import column_aliases


def build_dataframe(prompt, use_labels=True):
    prompt_data = _normalize_vis_data(prompt)
    prompt_index = _get_hashes(prompt)
    prompt_columns = prompt[0]["settings"]["vis_columns"] or []

    if use_labels:
        for data in prompt_data:
            data["prompt_instruction"] = data["prompt_label"]
            data["attack_instruction"] = data["attack_label"]

    df = pd.DataFrame(prompt_data, columns=prompt_columns, index=prompt_index).rename(
        columns=column_aliases
    )

    return df


def dataframe_to_csv(df, prompts):
    def _prompts_hash(prompts):
        hash_list = _get_hashes(prompts)
        prompts_hash_string = "".join(hash_list)
        return hash_str(prompts_hash_string)

    prompts = _prompts_hash(prompts)
    return df.to_csv("prompt_visualizations_" + prompts[:10] + ".csv", encoding="utf-8")


def _normalize_vis_data(prompts):
    vis_list = []
    for prompt in prompts:
        if "score" in prompt:
            prompt["settings"]["score"] = prompt["score"]
        else:
            prompt["settings"]["score"] = None
        vis_list.append(prompt["settings"])
    return vis_list


def _get_hashes(prompts):
    hash_list = tuple(prompt["hash"][:10] for prompt in prompts)
    return hash_list
