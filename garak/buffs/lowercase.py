#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) <year> NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


""" Buff that converts prompts to lower case. """

from collections.abc import Iterable
from typing import List

import garak.attempt
from garak.buffs.base import Buff

class Lowercase(Buff):
    """ Lowercasing buff """

    def buff(source_attempts: List[garak.attempt.Attempt]) -> Iterable[garak.attempt.Attempt]:
        for source_attempt in source_attempts:
            lowercase_attempt = self._derive_new_attempt(attempt)
            lowercase_attempt.prompt = lowercase_attempt.prompt.lower()
            yield lowercase_attempt

