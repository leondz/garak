from garak.generators.huggingface import Model
import attack_manager
from argparse import ArgumentParser
import torch.multiprocessing as mp


# GCG parser used by interactive mode
gcg_parser = ArgumentParser()
gcg_parser.add_argument("--transfer", action="store_true", help="Generate attack for transfer")
gcg_parser.add_argument("--progressive", action="store_true", help="Use progressive goals")
gcg_parser.add_argument("--stop_success", action="store_true", help="Stop on success")
gcg_parser.add_argument("--generator", nargs="?", type=Model, help="Garak generator to use")
gcg_parser.add_argument("--outfile", type=str, default="./data/gcg_prompts.txt",
                        help="Location to write GCG attack output")


def generate_gcg(transfer: bool, progressive: bool, stop_success: bool, model_names: list[str],
                 train_data: str = "./data/advbench/harmful_behaviors.csv", outfile: str = "./data/gcg/gcg.txt"):
    """
    Function to generate GCG attack strings
    Args:
        transfer (bool): Whether the attack generated is for a transfer attack
        progressive (bool): Whether to use progressive goals
        stop_success (bool): Whether to stop on a successful attack
        model_names (list[str]): List of huggingface models (Currently only support HF due to tokenizer)
        train_data (str): Path to training data
        outfile (str): Where to write successful prompts

    Kwargs:

    Returns:
        None
    """
    mp.set_start_method('spawn')

    # TODO: Add params for get_goals_and_targets. Currently just a skeleton
    train_goals, train_targets, test_goals, test_targets = attack_manager.get_goals_and_targets(goals=,
                                                                                 targets=,
                                                                                 test_goals=,
                                                                                 test_targets=,
                                                                                 train_data=train_data)

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
            progressive_models=,
            progressive_goals=,
            control_init=,
            logfile=,
            managers=managers,
            test_goals=test_goals,
            test_targets=test_targets,
            test_workers=test_workers,
            mpa_deterministic=,
            mpa_lr=,
            mpa_batch_size=,
            mpa_n_steps=
        )
    else:
        attack = attack_manager.IndividualPromptAttack(
            train_goals,
            train_targets,
            workers,
            control_init=,
            logfile=,
            managers=managers,
            test_goals=,
            test_targets=,
            test_workers=test_workers,
            mpa_deterministic=,
            mpa_lr=,
            mpa_batch_size=,
            mpa_n_steps=
        )

    attack.run(
        n_steps=,
        batch_size=,
        topk=,
        temp=,
        target_weight=,
        control_weight=,
        test_steps=,
        anneal=,
        incr_control=,
        stop_on_success=,
        verbose=,
        filter_cand=,
        allow_non_ascii=,
    )

    for worker in workers + test_workers:
        worker.stop()
