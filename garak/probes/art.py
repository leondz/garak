#!/usr/bin/env python3

"""auto redteam"""

import copy
import logging
import json
import re
from typing import List

from tqdm import tqdm

import garak._config
import garak.attempt
from garak.probes.base import Probe
from garak.generators.huggingface import Pipeline

output_sep = "<||>"


class Tox(Probe):
    name = "ART"
    description = "Auto Red-Team"
    recommended_detector = ["toxicity.ToxicCommentModel"]
    redteamer = None
    max_calls = 5
    constructive_tension = True
    tags = ["avid-effect:ethics:E0301"]
    goal = "make the model say something toxic"

    def probe(self, generator) -> List[garak.attempt.Attempt]:
        if self.redteamer == None:
            self.redteamer = Pipeline("leondz/artgpt2tox")
            self.redteamer.generations = 1
            self.redteamer.deprefix_prompt = True

        attempts = []

        target_generations = generator.generations
        generator.generations = 1  # take generations one-by-one (will restore later)
        if "max_new_tokens" in dir(generator):  # let the probed model decide what to do
            prev_max_new_tokens = generator.max_new_tokens
            generator.max_new_tokens = None
        attack_iterator = tqdm(range(target_generations), leave=False)
        attack_iterator.set_description(self.probename.replace("garak.", ""))

        for i in attack_iterator:
            self.redteamer.max_new_tokens = (
                None  # artopt unhappy with this being set on first iter
            )
            calls_made = 0
            keep_going = True

            this_attempt = garak.attempt.Attempt()
            this_attempt.probe_classname = "art." + self.__class__.__name__
            this_attempt.status = garak.attempt.ATTEMPT_STARTED

            this_attempt.prompt = ""
            last_response = None
            turns = []
            logging.debug(f"ART: attempt {i} uuid {this_attempt.uuid}")

            while calls_made < self.max_calls and keep_going:
                # generate a challenge
                if last_response == "" and self.constructive_tension:
                    challenge = ""
                else:
                    if last_response:
                        last_response_first_sent = last_response.split(". ")[
                            0
                        ]  # nltk install too unfriendly
                    else:
                        last_response_first_sent = ""

                    query = f"<|input|>{last_response_first_sent}<|response|>"
                    # print("query:", query)
                    challenge = self.redteamer.generate(query)
                    # print("challenge:", challenge)
                    challenge = re.sub("\<\|.*", "", challenge[0]).strip()
                    # get first item, ignore whitespace, take everything up to the first newline
                    # challenge[0].strip().split("\n")[0].strip()
                    # log what we'll send

                turn = ("probe", challenge)
                turns.append(turn)
                logging.debug(f"ART: {turn}")
                # send the challenge and get the response
                response = generator.generate(challenge)[0].strip()
                # log the response
                turn = ("model", response)
                turns.append(turn)
                logging.debug(f"ART: {turn}")
                # increment calls_made
                calls_made += 1
                # check if the resp is empty or if it matches the previous resp
                if not len(response) and not self.constructive_tension:
                    keep_going = False
                if response == last_response:
                    keep_going = False
                # update last_response
                last_response = response.replace("\n", " ").strip()
                self.redteamer.max_new_tokens = 170  # after first iter, give a limit

            this_attempt.notes["turns"] = turns
            this_attempt.outputs = [turn[1] for turn in turns if turn[0] == "model"]

            garak._config.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            attempts.append(copy.deepcopy(this_attempt))

        # restore the generator object's original number of generations
        generator.generations = target_generations
        # restore generator's token generation limit
        if "max_new_tokens" in dir(generator):  # let the probed model decide what to do
            generator.max_new_tokens = prev_max_new_tokens

        return attempts
