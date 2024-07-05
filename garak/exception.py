# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0


class GarakException(Exception):
    """Base class for all  garak exceptions"""

    pass


class APIKeyMissingError(GarakException):
    """Exception to be raised if a required API key is not found"""

    pass


class ModelNameMissingError(GarakException):
    """A generator requires model_name to be set, but it wasn't"""

    pass


class GarakBackoffTrigger(GarakException):
    """Thrown when backoff should be triggered"""

    pass


class BadGeneratorException(GarakException):
    """Generator config/description is not usable"""

    pass


class RateLimitHit(Exception):
    """Raised when a rate limiting response is returned"""

    pass
