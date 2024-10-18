# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak.attempt import Attempt
from garak.generators.test import Lipsum
from garak.resources.red_team.evaluation import EvaluationJudge


class MockJudge(EvaluationJudge):

    name = "mockJudge"
    evaluation_generator = Lipsum(name="gpt-3.5-turbo")
    evaluator_token_limit = 1024
    system_prompt_judge = "fake prompt with a {goal}"
    system_prompt_on_topic = "fake prompt with a {goal}"


@pytest.fixture
def mockJudgeAndAttempt():
    g = MockJudge()
    a = Attempt(prompt="fake")
    a.outputs = ["result"]
    return g, a


def test_EvaluationJudge_judge_score(mockJudgeAndAttempt):
    g, a = mockJudgeAndAttempt
    g.judge_score(a.prompt, a.outputs)
    pass


def test_EvaluationJudge_on_topic_score(mockJudgeAndAttempt):
    g, a = mockJudgeAndAttempt
    g.on_topic_score(a.all_outputs)
    pass
