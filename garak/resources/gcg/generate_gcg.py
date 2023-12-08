# MIT License
#
# Copyright (c) 2023 Andy Zou
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from garak.generators.huggingface import Model
from garak.resources.gcg import attack_manager
from garak.resources.gcg import gcg_attack
from argparse import ArgumentParser
import torch.multiprocessing as mp
from datetime import datetime
from pathlib import Path
from logging import getLogger

CONTROL_INIT = "! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !"
PATH = Path(__file__).parents[0]


logger = getLogger(__name__)

# GCG parser used by interactive mode
gcg_parser = ArgumentParser()
gcg_parser.add_argument("--model_names", nargs="+", help="Model names for generation")
gcg_parser.add_argument(
    "--transfer", action="store_true", help="Whether to generate attack for transfer"
)
gcg_parser.add_argument(
    "--progressive", action="store_true", help="Use progressive goals"
)
gcg_parser.add_argument("--stop_success", action="store_true", help="Stop on success")
gcg_parser.add_argument(
    "--train_data",
    type=str,
    default=f"{PATH}/data/advbench/harmful_behaviors.csv",
    help="Path to training data",
)
gcg_parser.add_argument(
    "--n_train", type=int, default=50, help="Number of training samples to use"
)
gcg_parser.add_argument(
    "--n_test", type=int, default=0, help="Number of test samples to use"
)
gcg_parser.add_argument(
    "--outfile",
    type=str,
    default=f"{PATH}/data/gcg_prompts.txt",
    help="Location to write GCG attack output",
)
gcg_parser.add_argument(
    "--control_init", type=str, default=CONTROL_INIT, help="Initial control string"
)
gcg_parser.add_argument(
    "--n_steps", type=int, default=500, help="Number of steps for optimization"
)
gcg_parser.add_argument(
    "--batch_size", type=int, default=128, help="Optimization batch size"
)
gcg_parser.add_argument(
    "--allow_non_ascii",
    action="store_true",
    help="Allow non-ASCII characters in control string",
)
gcg_parser.add_argument(
    "--save_logs", action="store_true", help="Keep detailed GCG generation logs"
)


def generate_gcg(
    model_names: list[str],
    transfer: bool = False,
    progressive: bool = False,
    stop_success: bool = True,
    train_data: str = f"{PATH}/data/advbench/harmful_behaviors.csv",
    n_train: int = 50,
    n_test: int = 0,
    outfile: str = f"{PATH}/data/gcg/gcg.txt",
    control_init: str = CONTROL_INIT,
    deterministic: bool = True,
    n_steps: int = 500,
    batch_size: int = 128,
    topk: int = 256,
    temp: int = 1,
    target_weight: float = 1.0,
    control_weight: float = 0.0,
    test_steps: int = 50,
    anneal: bool = False,
    incr_control: bool = False,
    filter_cand: bool = True,
    allow_non_ascii: bool = False,
    lr: float = 0.01,
    save_logs: bool = False,
    **kwargs,
):
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
        save_logs (bool): Maintain GCG running logs

    Kwargs:
        test_data (str): Path to test data

    Returns:
        None
    """
    mp.set_start_method("spawn")

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

    logger.debug("Loading goals and targets for GCG attack.")
    (
        train_goals,
        train_targets,
        test_goals,
        test_targets,
    ) = attack_manager.get_goals_and_targets(
        train_data=train_data, test_data=test_data, n_train=n_train, n_test=n_test
    )

    logger.debug("Loading workers for GCG attack")
    # TODO: Specify additional args for get_workers
    workers, test_workers = attack_manager.get_workers(model_names=model_names)

    managers = {
        "AP": gcg_attack.GCGAttackPrompt,
        "PM": gcg_attack.GCGPromptManager,
        "MPA": gcg_attack.GCGMultiPromptAttack,
    }

    if transfer:
        attack = attack_manager.ProgressiveMultiPromptAttack(
            goals=train_goals,
            targets=train_targets,
            workers=workers,
            progressive_models=progressive,
            progressive_goals=progressive,
            control_init=control_init,
            logfile=logfile,
            outfile=outfile,
            managers=managers,
            test_goals=test_goals,
            test_targets=test_targets,
            test_workers=test_workers,
            mpa_deterministic=deterministic,
            mpa_lr=lr,
            mpa_batch_size=batch_size,
            mpa_n_steps=n_steps,
        )
    else:
        attack = attack_manager.IndividualPromptAttack(
            goals=train_goals,
            targets=train_targets,
            workers=workers,
            control_init=control_init,
            logfile=logfile,
            outfile=outfile,
            managers=managers,
            test_goals=test_goals,
            test_targets=test_targets,
            test_workers=test_workers,
            mpa_deterministic=deterministic,
            mpa_lr=lr,
            mpa_batch_size=batch_size,
            mpa_n_steps=n_steps,
        )

    if save_logs:
        logger.info(
            f"Beginning GCG generation, detailed logging information for this run is in {logfile}."
        )
    else:
        logger.info("Beginning GCG generation")
    attack.run(
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

    logger.debug("GCG generation complete!")

    if not save_logs:
        p = Path(logfile)
        p.unlink()
