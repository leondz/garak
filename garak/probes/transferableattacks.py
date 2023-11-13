"""transferableattacks

Creates universal, transferable adversarial attacks using the llm-attacks framework. 
(code: https://github.com/llm-attacks/llm-attacks/tree/main, paper: https://arxiv.org/abs/2307.15043)
Code is adapted from the llm-attacks repo to garak probes
"""

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from garak.attempt import Attempt
from garak.probes.base import Probe
