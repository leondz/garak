"""Known-bad signature detectors

These look for signatures designed to test various malicious content
detectors
"""

from garak import _config
from garak.detectors.base import StringDetector
import garak.probes.knownbadsignatures


class EICAR(StringDetector):
    """Is the EICAR test string present?"""

    matchtype = "str"
    tags = ["avid-effect:security:S0301"]

    def __init__(self, config_root=_config):
        self.substrings = [garak.probes.knownbadsignatures.EICAR_SIGNATURE]
        super().__init__(self.substrings, config_root=config_root)


class GTUBE(StringDetector):
    """Is the GTUBE test string present?"""

    matchtype = "str"
    tags = ["avid-effect:security:S0301"]

    def __init__(self, config_root=_config):
        self.substrings = [garak.probes.knownbadsignatures.GTUBE_SIGNATURE]
        super().__init__(self.substrings, config_root=config_root)


class GTphish(StringDetector):
    """Is the GTphish test string present?"""

    matchtype = "str"
    tags = ["avid-effect:security:S0301"]

    def __init__(self, config_root=_config):
        self.substrings = [garak.probes.knownbadsignatures.GTPHISH_SIGNATURE]
        super().__init__(self.substrings, config_root=config_root)
