# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from garak.attempt import Attempt
import garak.detectors.base
import garak.detectors.fileformats


def test_possiblepickle_init():
    d = garak.detectors.fileformats.PossiblePickleName()
    assert isinstance(d, garak.detectors.base.Detector)


def test_possiblepickle_filenames():
    d = garak.detectors.fileformats.PossiblePickleName()
    test_attempt = Attempt()
    test_attempt.outputs = [
        "config.json",
        "file.onnx",
        "file.pth",
        "model.pkl",
        "model.pickle",
        None,
    ]
    assert list(d.detect(test_attempt)) == [0.0, 0.0, 0.0, 1.0, 1.0]
