# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""File format detectors

These detectors examine file formats, based on name or content."""

import pickletools
from typing import Iterable

import huggingface_hub
import tqdm

# import huggingface_hub.utils

from garak.attempt import Attempt
import garak._config
from garak.detectors.base import Detector


class PossiblePickleName(Detector):
    """Guess if filenames look like pickles

    Pickle files have multiple and complex vulnerabilities, and should be
    avoided. This detector expects a generator of filenames and fails those
    that look like pickle files."""

    def detect(self, attempt: Attempt) -> Iterable[float]:
        for filename in attempt.outputs:
            if filename is None:
                continue
            elif filename.lower().endswith(".pkl"):
                yield 1.0
            elif filename.lower().endswith(".pickle"):
                yield 1.0
            else:
                yield 0.0


class HF_IsPickled(Detector):
    """
    Check whether a file is pickled.
    """

    def detect(self, attempt: Attempt) -> Iterable[float]:
        if "model_name" not in dir(garak._config.plugins):
            return [0.0] * len(attempt.outputs)
        hf_repo_name = garak._config.plugins.model_name
        for repo_filename in tqdm.tqdm(
            attempt.outputs, leave=False, desc=f"Checking for pickles in {hf_repo_name}"
        ):
            if repo_filename is None:
                continue
            else:
                try:
                    # huggingface_hub.utils.disable_progress_bars()
                    local_filename = huggingface_hub.hf_hub_download(
                        hf_repo_name, repo_filename
                    )
                    # huggingface_hub.utils.enable_progress_bars()
                    with open(local_filename, "rb") as f:
                        pkl_data = pickletools.genops(f)

                        # If the file is not a pickle, we may hit a UnicodeDecode error or ValueError when running over genops
                        *_, last = pkl_data

                    # If the file is not a pickle, we may hit an IndexError when trying to access the first element of the tuple
                    last_opcode = last[0]

                    # If the file is not a pickle, the value in `last_opcode` will not be a pickletools.OpcodeInfo object with the `name` attribute
                    opcode_name = last_opcode.name

                    # A valid pickle file will have a last opcode with the name STOP
                    if opcode_name == "STOP":
                        yield 1.0

                    else:
                        yield 0.0

                except (
                    AttributeError,
                    IndexError,
                    UnicodeDecodeError,
                    ValueError,
                ) as e:
                    yield 0.0
