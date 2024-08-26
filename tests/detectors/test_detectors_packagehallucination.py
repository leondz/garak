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
