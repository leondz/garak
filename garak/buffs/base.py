#!/usr/bin/env python3
"""Base classes for buffs.

Buff plugins augment, constrain, or otherwise perturb the interaction
between probes and a generator. Buffs must inherit this base class. 
`Buff` serves as a template showing what expectations there are for
implemented buffs. """

from typing import List

import garak.attempt

class Buff:
    """ Base class for a buff.

    A buff should take as input a list of attempts, and return
    a list of events. It should be able to return a generator.
    It's worth storing the origin attempt ID in the notes attrib
    of derivative attempt objects.
    """

    uri = ""
    bcp47 = None # set of languages this buff should be constrained to
    active = True

    def __init__(self) -> None:
        pass

    def _derive_new_attempt(source_attempt: garak.attempt.Attempt) -> garak.attempt.Attempt:
        new_attempt = garak.attempt.Attempt(
            status = source_attempt.status,
            prompt = source_attempt.prompt,
            probe_classname = source_attempt.probe_classname,
            probe_params = source_attempt.probe_params,
            targets = source_attempt.targets,
            outputs = source_attempt.outputs,
            notes = source_attempt.notes,
            detector_results = source_attempt.detector_results,
            goal = source_attempt.goal,
            seq = source_attempt.seq,
        )
        new_attempt.notes['buff_source_attempt_id'] = source_attempt.uuid
        new_attempt.notes['buff_creator'] = self.__class__.__name__

    def buff(source_attempts: List[garak.attempt.Attempt]) -> Iterable[garak.attempt.Attempt]:
        for attempt in source_attempts:
            yield self._derive_new_attempt(attempt)
