# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0


class APIKeyMissingError(Exception):
    """Exception to be raised if a required API key is not found"""

    pass


class ModelNameMissingError(Exception):
    """A generator requires model_name to be set, but it wasn't"""

    pass