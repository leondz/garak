import logging

from garak import _config, _plugins
from garak.harnesses import Harness
from garak.detectors import Detector

class DetectorOnly(Harness):
    def __init__(self, config_root=_config):
        super().__init__(config_root)

    def _load_detector(self, detector_name: str) -> Detector:
        detector = _plugins.load_plugin(
            detector_name, break_on_fail=False
        )
        if detector:
            return detector
        else:
            print(f" detector load failed: {detector_name}, skipping >>")
            logging.error(f" detector load failed: {detector_name}, skipping >>")
        return False

    def run(self, attempts, detector_names, evaluator):
        detectors = []
        for detector in sorted(detector_names):
            d = self._load_detector(detector)
            if d:
                detectors.append(d)

        if len(detectors) == 0:
            msg = "No detectors, nothing to do"
            logging.warning(msg)
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print(msg)
            raise ValueError(msg)

        super().run_detectors(detectors, attempts, evaluator) # The probe is None, but hopefully no errors occur with probe.