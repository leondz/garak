# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Management of payloads.

This module co-ordinates and provides for dynamic switching of "payloads"
with garak. Payloads are items intended for inserting in prompts, that
are intended to trigger a specific LLM behavior, or to be present in LLM output.

A payload can affect how we detect whether a probe was successful. For example,
for payloads intended to be repeated by the model, the detector should be one that
can pick up on a given string.

To be interchangeable between probes, paylaods are stored separately from
probes. The search priority path is:

    1. garak._config.transient.data_dir / "resources" / "payloads",
    2. garak._config.transient.package_dir / "resources" / "payloads",

That is, user payloads under XDG_DATA_DIR override those provided with garak.

The JSON structure of a payload is:

{
    "garak_payload_name": -- a mandatory key, used to identify this as a garak payload. holds a description of the payload.
    "payload_types": -- a list of strings, each identifying an entry in the payload typology (typology_payloads.tsv)
        ["Security circumvention instructions/Product activation codes"],
    "detector_name": "productkey.Win5x5", -- a suggested detector
    "detector_config": {}, -- a config dict of Configurable options for the detector
    "payloads": [ -- a list of strings: the payloads themselves
        "Windows 10",
        "Windows 10 Pro"
    ]
    "bcp47": "en" - * or a comma-separated list of bcp47 tags describing the languages this payload can be used with
}
"""


import json
import jsonschema
import logging
import pathlib
from typing import Generator, List, Union


import garak._config
import garak.exception


PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "garak_payload_name": {"type": "string"},
        "payload_types": {"type": "array", "items": {"type": "string"}},
        "detector_name": {"type": "string"},
        "detector_config": {"type": "object"},
        "payloads": {"type": "array", "items": {"type": "string"}},
        "bcp47": {"type": "string"},
    },
    "required": [
        "garak_payload_name",
        "payload_types",
        "payloads",
    ],
}

PAYLOAD_SEARCH_DIRS = [
    garak._config.transient.data_dir / "resources" / "payloads",
    garak._config.transient.package_dir / "resources" / "payloads",
]


def _validate_payload(payload_json):
    try:
        jsonschema.validate(instance=payload_json, schema=PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as ve:
        return ve
    return True


class PayloadGroup:
    """Represents a configured group of payloads for use with garak
    probes. Each group should have a name, one or more payload types, and
    a number of payload entries"""

    def _load(self):
        logging.debug("Loading payload %s from %s", self.name, self.path)
        try:
            with open(self.path, "r", encoding="utf-8") as payloadfile:
                loaded_payload = json.load(payloadfile)

        except FileNotFoundError as fnfe:
            msg = "Payload file not found:" + str(self.path)
            logging.error(msg, exc_info=fnfe)
            raise garak.exception.PayloadFailure(msg) from fnfe

        except json.JSONDecodeError as jde:
            msg = "Payload JSON error:" + str(jde)
            logging.error(msg, exc_info=jde)
            raise garak.exception.PayloadFailure("Payload JSON error") from jde

        validation_result = _validate_payload(loaded_payload)
        if validation_result is not True:
            msg = "Payload JSON schema mismatch:" + str(validation_result)
            logging.error(msg, exc_info=validation_result)
            raise garak.exception.PayloadFailure(
                "Payload didn't match schema"
            ) from validation_result

        self.types = loaded_payload["payload_types"]
        self.payloads = [str(p) for p in loaded_payload["payloads"]]

        self.detector_name = None
        if "detector_name" in loaded_payload:
            self.detector_name = str(loaded_payload["detector_name"])

        self.detector_config = None
        if "detector_config" in loaded_payload:
            try:
                self.detector_config = dict(loaded_payload["detector_config"])

            except TypeError as te:
                msg = "Payload detector_config must be a dict, got: " + repr(
                    loaded_payload["detector_config"]
                )
                logging.warning(msg, exc_info=te)
                raise garak.exception.PayloadFailure(msg) from te

        if garak._config.transient.reportfile is not None:
            garak._config.transient.reportfile.write(
                json.dumps(
                    {
                        "entry_type": "init",
                        "loading_complete": "payload",
                        "payload_name": self.name,
                        "payload_path": self.path,
                    }
                )
                + "\n"
            )
        self._loaded = True

    def __init__(self, name: str, path) -> None:
        self.name = str(name)
        self.path = path
        self.types = None
        self.payloads = None
        self.detector_name = None
        self.detector_params = None
        self._loaded = False
        self._load()


def _load_payload(
    name: str, path: Union[str, pathlib.Path, None] = None
) -> PayloadGroup:
    if path is not None:
        return PayloadGroup(name, path)
    else:
        # iterate through search dirs
        for dir in PAYLOAD_SEARCH_DIRS:
            path = pathlib.Path(dir) / f"{name}.json"
            if path.is_file():
                return PayloadGroup(name, path)
    raise FileNotFoundError(
        "File '%s.json' not found in payload search directories" % name
    )


class Loadmaster:
    """The payload Loadmaster manages payload groups. It'll inventory them on disk,
    manage enumeration of payloads (optionally given a payload type specification),
    and load them up."""

    def _scan_payload_dir(self, dir) -> dict:
        """Look for .json entries in a dir, load them, check which are
        payloads, return name:path dict. optionally filter by type prefixes"""

        payloads_found = {}
        dir = pathlib.Path(dir)
        if not dir.is_dir():
            return {}

        entries = dir.glob("**/*.[jJ][sS][oO][nN]")
        for payload_path in entries:
            with open(str(payload_path), "r", encoding="utf-8") as payload_path_file:
                try:
                    payload_decoded = json.load(payload_path_file)
                    payload_types = payload_decoded["payload_types"]
                except (json.JSONDecodeError, KeyError) as exc:
                    msg = f"Invalid payload, skipping: {payload_path}"
                    logging.debug(msg, exc_info=exc)
                    # raise garak.exception.PayloadFailure(msg) from exc

                payload_name = payload_path.stem

                payloads_found[payload_name] = {
                    "path": payload_path,
                    "types": payload_types,
                }

        return payloads_found

    def _refresh_payloads(self) -> None:
        """Scan resources/payloads and the XDG_DATA_DIR/payloads for
        payload objects, and refresh self.payload_list"""
        self.payload_list = {}
        for payload_dir in PAYLOAD_SEARCH_DIRS[
            ::-1
        ]:  # reverse order because | clobbers at top-level key
            self.payload_list = self.payload_list | self._scan_payload_dir(payload_dir)

    def search(
        self, types: Union[List[str], None] = None, include_children=True
    ) -> Generator[str, None, None]:
        """Return list of payload names, optionally filtered by types"""
        for payload in self.payload_list:
            if types is None:
                yield payload
            else:
                if include_children is False:
                    matches = [
                        payload_type == type_prefix
                        for payload_type in self.payload_list[payload]["types"]
                        for type_prefix in types
                    ]
                else:
                    matches = [
                        payload_type.startswith(type_prefix)
                        for payload_type in self.payload_list[payload]["types"]
                        for type_prefix in types
                    ]
                if any(matches):
                    yield payload

    def load(self, name) -> PayloadGroup:
        """Return a PayloadGroup"""
        try:
            path = self.payload_list[name]["path"]
            p = _load_payload(name, path)  # or raise KeyError

        except KeyError as ke:
            msg = f"Requested payload {name} is not registered in this Loadmaster"
            logging.error(msg, exc_info=ke)
            raise garak.exception.PayloadFailure(msg) from ke

        except FileNotFoundError as fnfe:
            msg = f"Requested payload {name} not found at expected path {path}"
            logging.error(msg, exc_info=fnfe)
            raise garak.exception.PayloadFailure(msg) from fnfe

        return p

    def __init__(self) -> None:
        self.payload_list = {}  # name: {path:path, types:types}
        self._refresh_payloads()
