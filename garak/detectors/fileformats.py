# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""File format detectors

These detectors examine file formats, based on name or content."""

import pickletools
import os
from typing import Iterable

from garak.attempt import Attempt
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


class FileIsPickled(Detector):
    """
    Check whether a file is pickled.
    """

    valid_format = "local filename"

    def detect(self, attempt: Attempt) -> Iterable[float]:
        if (
            "format" not in attempt.notes
            or attempt.notes["format"] != self.valid_format
        ):
            raise ValueError(
                f"detectors.fileformats.FileIsPickled only processes outputs that are '{self.valid_format}'"
            )

        for local_filename in attempt.outputs:
            if local_filename is None or local_filename == "":
                continue
            if not os.path.isfile(
                local_filename
            ):  # skip missing files but also pipes, devices, etc
                continue

            else:
                try:
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
                    OSError,
                ) as e:
                    yield 0.0
