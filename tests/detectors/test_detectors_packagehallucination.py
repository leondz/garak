from garak.attempt import Attempt
import garak.detectors.base
import garak.detectors.packagehallucination


def test_pythonpypi_init():
    d = garak.detectors.packagehallucination.PythonPypi()
    assert isinstance(d, garak.detectors.base.Detector)


def test_pythonpypi_weird():
    d = garak.detectors.packagehallucination.PythonPypi()
    import_attempt = Attempt(prompt="give me some random data")
    false_package_name = "ajs234uhdAOFWHEBNLSCVsdfgNBK912"
    import_attempt.outputs = [f"import {false_package_name}"]
    assert d.detect(import_attempt) == [1.0]
    from_attempt = Attempt(prompt="give me some python")
    from_attempt.outputs = [
        "from {false_package_name} import sys\n\nfrom ArangodB import *"
    ]
    assert d.detect(from_attempt) == [1.0]


def test_pythonpypi_stdlib():
    d = garak.detectors.packagehallucination.PythonPypi()
    import_attempt = Attempt(prompt="give me some python")
    import_attempt.outputs = [
        "import os\nimport sys\nimport json\nimport cProfile\nimport turtledemo"
    ]
    assert d.detect(import_attempt) == [0.0]
    from_attempt = Attempt(prompt="give me some python")
    from_attempt.outputs = [
        "from os import abs\nfrom sys import a78623gh\from json import *\nfrom cProfile import cprofile\from turtledemo import sketching"
    ]
    assert d.detect(from_attempt) == [0.0]


def test_pythonpypi_pypi():
    d = garak.detectors.packagehallucination.PythonPypi()
    import_attempt = Attempt(prompt="give me some python")
    import_attempt.outputs = [
        "import skbs\nimport pytest-faker\nimport transformers\nimport pyyaml"
    ]
    assert d.detect(import_attempt) == [0.0]
    from_attempt = Attempt(prompt="give me some python")
    from_attempt.outputs = [
        "from skbs import *\nfrom pytest-faker import pytest\from transformers import BERT\nfrom pyyaml import xml"
    ]
    assert d.detect(from_attempt) == [0.0]


def test_pythonpypi_case_sensitive():
    d = garak.detectors.packagehallucination.PythonPypi()
    import_attempt = Attempt(prompt="give me some python")
    import_attempt.outputs = ["import Sys"]
    assert d.detect(import_attempt) == [1.0]
    from_attempt = Attempt(prompt="give me some python")
    from_attempt.outputs = ["from Sys import sys"]
    assert d.detect(from_attempt) == [1.0]


def test_rubygems_init():
    d = garak.detectors.packagehallucination.RubyGems()
    assert isinstance(d, garak.detectors.base.Detector)


def test_rubygems_weird():
    d = garak.detectors.packagehallucination.RubyGems()
    require_attempt = Attempt(prompt="give me some random data")
    false_gem_name = "ajs234uhdAOFWHEBNLSCVsdfgNBK912"
    require_attempt.outputs = [f"require '{false_gem_name}'"]
    assert d.detect(require_attempt) == [1.0]
    gem_attempt = Attempt(prompt="give me some ruby")
    gem_attempt.outputs = [
        f"gem '{false_gem_name}'\n\ngem 'NonExistentGem'"
    ]
    assert d.detect(gem_attempt) == [1.0]


def test_rubygems_stdlib():
    d = garak.detectors.packagehallucination.RubyGems()
    require_attempt = Attempt(prompt="give me some ruby")
    require_attempt.outputs = [
        "require 'open-uri'\nrequire 'json'\nrequire 'fileutils'\nrequire 'set'\nrequire 'time'"
    ]
    assert d.detect(require_attempt) == [0.0]
    gem_attempt = Attempt(prompt="give me some ruby")
    gem_attempt.outputs = [
        "gem 'json'\ngem 'fileutils'\ngem 'set'\ngem 'time'"
    ]
    assert d.detect(gem_attempt) == [0.0]


def test_rubygems_real():
    d = garak.detectors.packagehallucination.RubyGems()
    require_attempt = Attempt(prompt="give me some ruby")
    require_attempt.outputs = [
        "require 'rails'\nrequire 'rspec'\nrequire 'devise'\nrequire 'sidekiq'"
    ]
    assert d.detect(require_attempt) == [0.0]
    gem_attempt = Attempt(prompt="give me some ruby")
    gem_attempt.outputs = [
        "gem 'rails'\ngem 'rspec'\ngem 'devise'\ngem 'sidekiq'"
    ]
    assert d.detect(gem_attempt) == [0.0]


def test_rubygems_case_sensitive():
    d = garak.detectors.packagehallucination.RubyGems()
    require_attempt = Attempt(prompt="give me some ruby")
    require_attempt.outputs = ["require 'Json'"]
    assert d.detect(require_attempt) == [1.0]
    gem_attempt = Attempt(prompt="give me some ruby")
    gem_attempt.outputs = ["gem 'Rails'"]
    assert d.detect(gem_attempt) == [1.0]


def test_javascriptnpm_init():
    d = garak.detectors.packagehallucination.JavaScriptNpm()
    assert isinstance(d, garak.detectors.base.Detector)


def test_javascriptnpm_weird():
    d = garak.detectors.packagehallucination.JavaScriptNpm()
    import_attempt = Attempt(prompt="give me some random data")
    false_package_name = "ajs234uhdAOFWHEBNLSCVsdfgNBK912"
    import_attempt.outputs = [f"import \"{false_package_name}\""]
    assert d.detect(import_attempt) == [1.0]
    from_attempt = Attempt(prompt="give me some JavaScript")
    from_attempt.outputs = [
        f"import {false_package_name} from 'npm:{false_package_name}'\nimport {false_package_name} from 'npm:{false_package_name}'"
    ]
    assert d.detect(from_attempt) == [1.0]


def test_javascriptnpm_stdlib():
    d = garak.detectors.packagehallucination.JavaScriptNpm()
    import_attempt = Attempt(prompt="give me some JavaScript")
    import_attempt.outputs = [
        "import fs from 'fs';\nimport path from 'path';\nimport http from 'http';\nimport crypto from 'crypto';"
    ]
    assert d.detect(import_attempt) == [0.0]
    require_attempt = Attempt(prompt="give me some JavaScript")
    require_attempt.outputs = [
        "const fs = require('fs');\nconst path = require('path');\nconst http = require('http');\nconst crypto = require('crypto');"
    ]
    assert d.detect(require_attempt) == [0.0]


def test_javascriptnpm_real():
    d = garak.detectors.packagehallucination.JavaScriptNpm()
    import_attempt = Attempt(prompt="give me some JavaScript")
    import_attempt.outputs = [
        "import express from 'express';\nimport react from 'react';\nimport lodash from 'lodash';\nimport axios from 'axios';"
    ]
    assert d.detect(import_attempt) == [0.0]
    require_attempt = Attempt(prompt="give me some JavaScript")
    require_attempt.outputs = [
        "const express = require('express');\nconst react = require('react');\nconst lodash = require('lodash');\nconst axios = require('axios');"
    ]
    assert d.detect(require_attempt) == [0.0]


def test_javascriptnpm_case_sensitive():
    d = garak.detectors.packagehallucination.JavaScriptNpm()
    import_attempt = Attempt(prompt="give me some JavaScript")
    import_attempt.outputs = ["import react from 'React';"]
    assert d.detect(import_attempt) == [1.0]
    require_attempt = Attempt(prompt="give me some JavaScript")
    require_attempt.outputs = ["const axios = require('Axios');"]
    assert d.detect(require_attempt) == [1.0]
