# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import glob
from pathlib import Path
import pickle
import pytest
import tempfile

from garak.attempt import Attempt
import garak.detectors.base
import garak.detectors.fileformats


def test_possiblepickle_init():
    d = garak.detectors.fileformats.PossiblePickleName()
    assert isinstance(d, garak.detectors.base.Detector)


def test_possiblepickle_filenames():
    d = garak.detectors.fileformats.PossiblePickleName()
    test_attempt = Attempt(prompt="")
    test_attempt.outputs = [
        "config.json",
        "file.onnx",
        "file.pth",
        "model.pkl",
        "model.pickle",
        None,
    ]
    assert list(d.detect(test_attempt)) == [0.0, 0.0, 0.0, 1.0, 1.0]


def test_fileispickled_invalid_format():
    d = garak.detectors.fileformats.FileIsPickled()
    plain_attempt = Attempt(prompt="")
    plain_attempt.outputs = ["a", "b", "c"]
    with pytest.raises(
        ValueError
    ) as exc_info:  # should not process attempts without correct "format" note
        l = list(d.detect(plain_attempt))


def test_fileispickled_valid_format():
    d = garak.detectors.fileformats.FileIsPickled()
    file_attempt = Attempt(prompt="")
    file_attempt.notes["format"] = "local filename"
    file_attempt.outputs = [""]
    l = list(d.detect(file_attempt))
    assert l == []


def test_fileispickled_nonpickle():
    d = garak.detectors.fileformats.FileIsPickled()
    nonpickle_file_attempt = Attempt(prompt="")
    nonpickle_file_attempt.notes["format"] = "local filename"
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as nonpickle_file:
        nonpickle_file.write(
            "Do you know what the sad part is, Odo? I'm a very good tailor."
        )
        nonpickle_file.close()
        nonpickle_file_attempt.outputs = [nonpickle_file.name]
        l = list(d.detect(nonpickle_file_attempt))
        assert l == [0.0]


def test_fileispickled_pickle_default():
    d = garak.detectors.fileformats.FileIsPickled()
    pickle_file_attempt = Attempt(prompt="")
    pickle_file_attempt.notes["format"] = "local filename"
    with tempfile.NamedTemporaryFile(mode="wb+", delete=False) as pickle_file:
        test_data_struct = {"key": ["value", 37176]}
        pickle.dump(test_data_struct, pickle_file)
        pickle_file.close()
        pickle_file_attempt.outputs = [pickle_file.name]
        l = list(d.detect(pickle_file_attempt))
        assert l == [1.0]


pickle_versions = [0, 1, 2, 3, 4, 5]


@pytest.mark.parametrize("pickle_ver", pickle_versions)
def test_fileispickled_pickle_versioned(pickle_ver):
    d = garak.detectors.fileformats.FileIsPickled()
    pickle_file_attempt = Attempt(prompt="")
    pickle_file_attempt.notes["format"] = "local filename"
    with tempfile.NamedTemporaryFile(mode="wb+", delete=False) as pickle_file:
        test_data_struct = {"key": ["value", 37176]}
        pickle.Pickler(pickle_file, pickle_ver).dump(test_data_struct)
        pickle_file.close()
        pickle_file_attempt.outputs = [pickle_file.name]
        l = list(d.detect(pickle_file_attempt))
        assert l == [1.0]


def test_fileisexectuable_nonexec():
    exec_attempt = garak.attempt.Attempt(prompt="")
    exec_attempt.notes["format"] = "local filename"
    d = garak.detectors.fileformats.FileIsExecutable()
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as test_file:
        test_file.write("I'm a very good tailor.")
        test_file.close()
        exec_attempt.outputs = [test_file.name]
        results = d.detect(exec_attempt)
        assert list(results) == [0.0]


def test_fileisexectuable_exec():
    exec_attempt = garak.attempt.Attempt(prompt="")
    exec_attempt.notes["format"] = "local filename"
    path_prefix = Path("tests/resources/fileformats/exec_files/")
    exec_files = glob.glob(str(path_prefix / "*"))
    print(exec_files)
    exec_files.remove(str(path_prefix / "LICENSE"))
    d = garak.detectors.fileformats.FileIsExecutable()
    exec_attempt.outputs = exec_files
    results = d.detect(exec_attempt)
    assert list(results) == [1.0] * len(exec_files)