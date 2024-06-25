"""Defines the Attempt class, which encapsulates a prompt with metadata and results"""

from typing import Any, List
import uuid

(
    ATTEMPT_NEW,
    ATTEMPT_STARTED,
    ATTEMPT_COMPLETE,
) = range(3)

roles = {"system", "user", "assistant"}


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
    :param messages: conversation turn histories; list of list of dicts have the format {"role": role, "content": text}, with actor being something like "system", "user", "assistant"
    :type messages: List(dict)

    Expected use
    * an attempt tracks a seed prompt and responses to it
    * there's a 1:1 relationship between attempts and source prompts
    * attempts track all generations
    * this means messages tracks many histories, one per generation
    * for compatibility, setting Attempt.prompt will set just one turn, and this is unpacked later
      when output is set; we don't know the # generations to expect until some output arrives
    * to keep alignment, generators need to return aligned lists of length #generations

    Patterns/expectations for Attempt access:
    .prompt - returns the first user prompt
    .outputs - returns the most recent model outputs
    .latest_prompts - returns a list of the latest user prompts

    Patterns/expectations for Attempt setting:
    .prompt - sets the first prompt, or fails if this has already been done
    .outputs - sets a new layer of model responses. silently handles expansion of prompt to multiple histories
    .latest_prompts - adds a new set of user prompts


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
        messages=None,
    ) -> None:
        self.uuid = uuid.uuid4()
        self.status = status
        if prompt is not None:
            self.prompt = prompt
        self.probe_classname = probe_classname
        self.probe_params = {} if probe_params is None else probe_params
        self.targets = [] if targets is None else targets
        # self.outputs = [] if outputs is None else outputs
        self.notes = {} if notes is None else notes
        self.detector_results = {} if detector_results is None else detector_results
        self.goal = goal
        self.seq = seq
        self.messages = [] if messages is None else messages

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
            "messages": self.messages,
        }

    def __getattribute__(self, name: str) -> Any:
        """override prompt and outputs access to take from history"""
        if name == "prompt":
            if len(self.messages) == 0:  # nothing set
                return None
            if isinstance(self.messages[0], dict):  # only initial prompt set
                return self.messages[0]["content"]
            if isinstance(
                self.messages, list
            ):  # there's initial prompt plus some history
                return self.messages[0][0]["content"]
            else:
                raise ValueError(
                    "Message history of attempt uuid %s in unexpected state, sorry: "
                    % str(self.uuid)
                    + repr(self.messages)
                )

        elif name == "outputs":
            if len(self.messages) and isinstance(self.messages[0], list):
                # work out last_output_turn that was assistant
                last_output_turn = max(
                    [
                        idx
                        for idx, val in enumerate(self.messages[0])
                        if val["role"] == "assistant"
                    ]
                )
                # return these (via list compr)
                return [m[last_output_turn]["content"] for m in self.messages]
            else:
                return []

        elif name == "latest_prompts":
            if len(self.messages) > 1:
                # work out last_output_turn that was assistant
                last_output_turn = max(
                    [
                        idx
                        for idx, val in enumerate(self.messages[0])
                        if val["role"] == "user"
                    ]
                )
                # return these (via list compr)
                return [m[last_output_turn]["content"] for m in self.messages]
            else:
                return (
                    self.prompt
                )  # returning a string instead of a list tips us off that generation count is not yet known

        else:
            return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """override prompt and outputs access to take from history
        NB. output elements need to be able to be None
        """
        if name == "prompt":
            assert isinstance(value, str)
            self.add_first_turn("user", value)

        elif name == "outputs":
            assert isinstance(value, list)
            # do we have only one prompt? in which case, let's flesh out messages a bit
            if len(self.messages) == 1:
                base_message = dict(self.messages[0])
                self.messages = [[base_message] for i in range(len(value))]
            elif len(self.messages) == 0:
                raise ValueError(
                    "Message histories need prompt to be set before outputs can be set"
                )
            # append each list item to each history, with role:assistant
            self.add_turns("assistant", value)

        elif name == "latest_prompts":
            assert isinstance(value, list)
            self.add_turns("user", value)

        else:
            return super().__setattr__(name, value)

    def add_first_turn(self, role: str, content: str) -> None:
        if self.messages != []:
            raise ValueError(
                "Cannot set prompt of attempt uuid %s with content already in message history: "
                % str(self.uuid)
                + repr(self.messages)
            )
        if role in roles:
            self.messages.append({"role": role, "content": content})
            return
        raise ValueError(
            "Conversation turn role must be one of '%s', got '%s'"
            % ("'/'".join(roles), role)
        )

    def add_turns(self, role: str, contents: List[str]) -> None:
        if len(contents) != len(self.messages):
            raise ValueError(
                "Message history misalignment in attempt uuid %s: tried to add %d items to %d message histories"
                % (str(self.uuid), len(contents), len(self.messages))
            )
        if role == "user" and (
            len(self.messages) == 0 or isinstance(self.messages[0], dict)
        ):
            raise ValueError(
                "can only add a list of user prompts after at least one system generation, so that generations count is known"
            )
        if role in roles:
            for idx, entry in enumerate(contents):
                self.messages[idx].append({"role": role, "content": entry})
            return
        raise ValueError(
            "Conversation turn role must be one of '%s', got '%s'"
            % ("'/'".join(roles), role)
        )
