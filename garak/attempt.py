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

    def as_dict(self) -> dict:
        return {
            "uuid": str(self.uuid),
            "status": self.status,
            "probe_classname": self.probe_classname,
            "probe_params": self.probe_params,
            "targets": self.targets,
            "prompt": self.prompt,
            "outputs": self.outputs,
            "notes": self.notes,
            "detector_results": self.detector_results,
        }
