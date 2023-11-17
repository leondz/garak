from garak.generators.huggingface import Model
import attack_manager
from argparse import ArgumentParser
import torch.multiprocessing as mp
from datetime import datetime
from pathlib import Path

CONTROL_INIT = "! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !"
PATH = Path(__file__).parents[0]


# GCG parser used by interactive mode
gcg_parser = ArgumentParser()
gcg_parser.add_argument("--transfer", action="store_true", help="Generate attack for transfer")
gcg_parser.add_argument("--progressive", action="store_true", help="Use progressive goals")
gcg_parser.add_argument("--stop_success", action="store_true", help="Stop on success")
gcg_parser.add_argument("--generator", nargs="?", type=Model, help="Garak generator to use")
gcg_parser.add_argument("--outfile", type=str, default="./data/gcg_prompts.txt",
                        help="Location to write GCG attack output")


def generate_gcg(model_names: list[str], transfer: bool = False, progressive: bool = False, stop_success: bool = False,
                 train_data: str = f"{PATH}/data/advbench/harmful_behaviors.csv", n_train: int = 50, n_test: int = 0,
                 outfile: str = f"{PATH}/data/gcg/gcg.txt", control_init = CONTROL_INIT, deterministic: bool = True,
                 n_steps: int = 500, batch_size: int = 32, topk: int = 256, temp: int = 1, target_weight: float = 1.0,
                 control_weight: float = 0.0, test_steps: int = 50, anneal: bool = False, incr_control: bool = False,
                 filter_cand: bool = True, allow_non_ascii: bool = False, lr: float = 0.01, **kwargs):
    """
    Function to generate GCG attack strings
    Args:
        transfer (bool): Whether the attack generated is for a transfer attack
        progressive (bool): Whether to use progressive goals
        stop_success (bool): Whether to stop on a successful attack
        model_names (list[str]): List of huggingface models (Currently only support HF due to tokenizer)
        train_data (str): Path to training data
        n_train (int): Number of training examples to use
        n_test (int): Number of test examples to use
        outfile (str): Where to write successful prompts
        control_init (str): Initial adversarial suffix to modify
        deterministic (bool): Whether or not to use deterministic gbda
        n_steps (int): Number of training steps
        batch_size(int):  Training batch size
        topk (int): Model hyperparameter for top k
        temp (int): Model temperature hyperparameter
        target_weight (float):
        control_weight (float):
        test_steps (int): Number of testing steps
        anneal (bool): Whether to use annealing
        incr_control (bool):
        filter_cand (bool):
        allow_non_ascii (bool): Allow non-ASCII test in adversarial suffixes
        lr (float): Model learning rate

    Kwargs:
        test_data (str): Path to test data

    Returns:
        None
    """
    mp.set_start_method('spawn')

    if "test_data" in kwargs:
        test_data = kwargs["test_data"]
    else:
        test_data = None

    if "logfile" in kwargs:
        logfile = kwargs["logfile"]
    else:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        model_string = "_".join([x.replace("/", "-") for x in model_names])
        logfile = f"{PATH}/data/logs/{timestamp}_{model_string}.json"

    # TODO: Add params for get_goals_and_targets. Currently just a skeleton
    train_goals, train_targets, test_goals, test_targets = attack_manager.get_goals_and_targets(train_data=train_data,
                                                                                                test_data=test_data,
                                                                                                n_train=n_train,
                                                                                                n_test=n_test)

    # TODO: Specify additional args for get_workers
    workers, test_workers = attack_manager.get_workers(model_names=model_names)

    managers = {
        "AP": attack_manager.AttackPrompt,
        "PM": attack_manager.PromptManager,
        "MPA": attack_manager.MultiPromptAttack,
    }

    if transfer:
        attack = attack_manager.ProgressiveMultiPromptAttack(
            train_goals,
            train_targets,
            workers,
            progressive_models=progressive,
            progressive_goals=progressive,
            control_init=control_init,
            logfile=logfile,
            managers=managers,
            test_goals=test_goals,
            test_targets=test_targets,
            test_workers=test_workers,
            mpa_deterministic=deterministic,
            mpa_lr=lr,
            mpa_batch_size=batch_size,
            mpa_n_steps=n_steps
        )
    else:
        attack = attack_manager.IndividualPromptAttack(
            train_goals,
            train_targets,
            workers,
            control_init=control_init,
            logfile=logfile,
            managers=managers,
            test_goals=test_goals,
            test_targets=test_targets,
            test_workers=test_workers,
            mpa_deterministic=deterministic,
            mpa_lr=lr,
            mpa_batch_size=batch_size,
            mpa_n_steps=n_steps
        )

    control_string, steps = attack.run(
        n_steps=n_steps,
        batch_size=batch_size,
        topk=topk,
        temp=temp,
        target_weight=target_weight,
        control_weight=control_weight,
        test_steps=test_steps,
        anneal=anneal,
        incr_control=incr_control,
        stop_on_success=stop_success,
        filter_cand=filter_cand,
        allow_non_ascii=allow_non_ascii,
    )

    for worker in workers + test_workers:
        worker.stop()
