import attack_manager
from garak.generators import Generator, load_generator
from attack_manager import get_goals_and_targets
from argparse import ArgumentParser


# GCG parser used by interactive mode
gcg_parser = ArgumentParser()
gcg_parser.add_argument("--transfer", action="store_true", help="Generate attack for transfer")
gcg_parser.add_argument("--progressive", action="store_true", help="Use progressive goals")
gcg_parser.add_argument("--stop_success", action="store_true", help="Stop on success")
gcg_parser.add_argument("--generator", nargs="?", type=Generator, help="Garak generator to use")
gcg_parser.add_argument("--outfile", type=str, default="./data/gcg_prompts.txt",
                        help="Location to write GCG attack output")


def generate_gcg(transfer: bool, progressive: bool, stop_success: bool, generator: Generator, attack: str,
                 train_data: str = "./data/advbench/harmful_behaviors.csv", outfile: str = "./data/gcg/gcg.txt"):
    """
    Function to generate GCG attack strings
    Args:
        transfer (bool): Whether the attack generated is for a transfer attack
        progressive (bool): Whether to use progressive goals
        stop_success (bool): Whether to stop on a successful attack
        generator (Generator): Garak Generator (currently only supports huggingface models)
        attack (str): What attack type to use
        train_data (str): Path to training data
        outfile (str): Where to write successful prompts

    Kwargs:

    Returns:
        None
    """
    pass