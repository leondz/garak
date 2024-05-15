"""Defines the Attempt class, which encapsulates a prompt with metadata and results"""

import uuid

(
    ATTEMPT_NEW,
    ATTEMPT_STARTED,
    ATTEMPT_COMPLETE,
) = range(3)


class Attempt:
    """A class defining objects that represent everything that constitutes
    a single attempt at evaluating an LLM.

    :param status: The status of this attempt; ``ATTEMPT_NEW``, ``ATTEMPT_STARTED``, or ``ATTEMPT_COMPLETE``
    :type status: int
    :param prompt: The processed prompt that will presented to the generator
    :type prompt: str
    :param probe_classname: Name of the probe class that originated this ``Attempt``
    :type probe_classname: str
    :param probe_params: Non-default parameters logged by the probe
    :type probe_params: dict, optional
    :param targets: A list of target strings to be searched for in generator responses to this attempt's prompt
    :type targets: List(str), optional
    :param outputs: The outputs from the generator in response to the prompt
    :type outputs: List(str)
    :param notes: A free-form dictionary of notes accompanying the attempt
    :type notes: dict
    :param detector_results: A dictionary of detector scores, keyed by detector name, where each value is a list of scores corresponding to each of the generator output strings in ``outputs``
    :type detector_results: dict
    :param goal: Free-text simple description of the goal of this attempt, set by the originating probe
    :type goal: str
    :param seq: Sequence number (starting 0) set in :meth:`garak.probes.base.Probe.probe`, to allow matching individual prompts with lists of answers/targets or other post-hoc ordering and keying
    :type seq: int
    """

    def __init__(
        self,
        status=ATTEMPT_NEW,
        prompt=None,
        probe_classname=None,
        probe_params=None,
        targets=None,
        outputs=None,
        notes=None,
        detector_results=None,
        goal=None,
        seq=-1,
    ) -> None:
        self.uuid = uuid.uuid4()
        self.status = status
        self.prompt = prompt
        self.probe_classname = probe_classname
        if probe_params is None:
            self.probe_params = {}
        else:
            self.probe_params = probe_params
        if targets is None:
            self.targets = []
        else:
            self.targets = targets
        if outputs is None:
            self.outputs = []
        else:
            self.outputs = outputs
        if notes is None:
            self.notes = {}
        else:
            self.notes = notes
        if detector_results is None:
            self.detector_results = {}
        else:
            self.detector_results = detector_results
        self.goal = goal
        self.seq = seq

    def as_dict(self) -> dict:
        """Converts the attempt to a dictionary."""
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
