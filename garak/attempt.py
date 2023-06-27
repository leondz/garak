#!/usr/bin/env python3

import uuid

(
    ATTEMPT_NEW,
    ATTEMPT_STARTED,
    ATTEMPT_COMPLETE,
) = range(3)


class Attempt:
    """A class defining objects that represent everything that constitutes
    a single attempt at evaluating an LLM.
    """

    def __init__(self) -> None:
        self.uuid = uuid.uuid4()
        self.status = ATTEMPT_NEW
        self.prompt = None
        self.probe_classname = None
        self.probe_params = {}
        self.targets = None
        self.outputs = []
        self.notes = {}
        self.detector_results = {}
        self.goal = None
        self.seq = -1

    def as_dict(self) -> dict:
        return {
            "entry_type": "attempt",
            "uuid": str(self.uuid),
            "seq": self.seq,
            "status": self.status,
            "probe_classname": self.probe_classname,
            "probe_params": self.probe_params,
            "targets": self.targets,
            "prompt": self.prompt,
            "outputs": list(self.outputs),
            "detector_results": self.detector_results,
            "notes": self.notes,
            "goal": self.goal,
        }
