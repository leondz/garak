# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# load default
# load non-existing
# load empty
# lookup absent combo
# calc valid zscore
# calc zscore w/ s.d. 0
# check comment assignment
# check dc assignment

import pytest

import garak.analyze.calibration


def test_instantiate():
    c = garak.analyze.calibration.Calibration()
    assert isinstance(c, garak.analyze.calibration.Calibration)


def test_load_default():
    c = garak.analyze.calibration.Calibration()
    c.load_calibration()
    assert isinstance(c._data, dict)


def test_load_constructor_explicit_absent():
    c = garak.analyze.calibration.Calibration("akshjdfiojavpoij")
    c.load_calibration()
    assert isinstance(c._data, dict)
    c = garak.analyze.calibration.Calibration("")
    c.load_calibration()
    assert isinstance(c._data, dict)


def test_load_load_explicit_absent():
    c = garak.analyze.calibration.Calibration()
    load_result = c.load_calibration("akshjdfiojavpoij")
    assert isinstance(c._data, dict)
    assert load_result is None


def test_data_before_load():
    c = garak.analyze.calibration.Calibration()
    assert c._data == {}
    assert c.metadata is None


def test_data_after_failed_load():
    c = garak.analyze.calibration.Calibration("alshdfohasdgih")
    c.load_calibration()
    assert c._data == {}
    assert c.metadata is None


def test_lookup_absent():
    c = garak.analyze.calibration.Calibration()
    c.load_calibration()
    z = c.get_z_score("a", "b", "c", "d", 50)
    assert z is None


def test_calc_z_score():
    c = garak.analyze.calibration.Calibration()
    assert c._calc_z(0.5, 0.1, 0.5) == 0
    assert c._calc_z(0.2, 0.2, 0.0) == -1
    with pytest.raises(ZeroDivisionError) as e:
        c._calc_z(0.4, 0.0, 0.9)


@pytest.mark.parametrize("defcon", [1, 2, 3, 4, 5])
def test_comments_written(defcon):
    assert isinstance(garak.analyze.calibration.ZSCORE_COMMENTS[defcon], str)
    assert garak.analyze.calibration.ZSCORE_COMMENTS[defcon] != ""


@pytest.mark.parametrize(
    "z", [0.0, -1.0, 1.0, -100000.0, 100000.0, 0.000001, 0.5, -0.5]
)
def test_defcon_comment(z):
    c = garak.analyze.calibration.Calibration()
    defcon, comment = c.defcon_and_comment(z)
    assert isinstance(defcon, int)
    assert isinstance(comment, str)
    assert 1 <= defcon <= 5
    assert comment == garak.analyze.calibration.ZSCORE_COMMENTS[defcon]
