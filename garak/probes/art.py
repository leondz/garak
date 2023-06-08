#!/usr/bin/env python3

"""auto redteam"""

import logging
from typing import List

import nltk
from tqdm import tqdm

import garak.attempt
from garak.probes.base import Probe
from garak.generators.huggingface import InferenceAPI

output_sep = "<||>"


class Tox(Probe):
    def __init__(self):
        self.name = ""
        super().__init__()
        self.recommended_detector = ["toxicity.ToxicCommentModel"]
        self.redteamer = None
        self.max_calls = 5

    def probe(self, generator) -> List[garak.attempt.Attempt]:
        if self.redteamer == None:
            self.redteamer = InferenceAPI("leondz/artopttox350m")
            self.redteamer.generations = 1

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
            this_attempt.probe_classname = self.__class__.__name__
            this_attempt.status = garak.attempt.ATTEMPT_STARTED

            this_attempt.prompt = ""
            last_response = ""
            turns = []

            while calls_made < self.max_calls and keep_going:
                # generate a challenge
                if last_response:
                    last_response_first_sent = nltk.sent_tokenize(last_response)[0]
                else:
                    last_response_first_sent = ""
                query = f"<|input|>{last_response_first_sent}<|response|>"
                challenge = self.redteamer.generate(query)
                challenge = (
                    challenge[0].strip().split("\n")[0].strip()
                )  # get first item, ignore whitespace, take everything up to the first newline
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
                if not len(response) or response == last_response:
                    keep_going = False
                # update last_response
                last_response = response.replace("\n", " ")
                self.redteamer.max_new_tokens = 150  # after first iter, give a limit

            this_attempt.notes["turns"] = turns
            this_attempt.outputs.append(
                output_sep
                + f"\n{output_sep}".join(
                    [turn[1] for turn in turns if turn[0] == "model"]
                )
            )

            _config.reportfile.write(json.dumps(this_attempt.as_dict()) + "\n")
            attempts.append(copy.deepcopy(this_attempt))

        # restore the generator object's original number of generations
        generator.generations = target_generations
        # restore generator's token generation limit
        if "max_new_tokens" in dir(generator):  # let the probed model decide what to do
            generator.max_new_tokens = prev_max_new_tokens

        return attempts
