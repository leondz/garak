"""Riskywords detector

A range of word-list based detectors, doing keyword matching
"""

from collections import defaultdict
import csv

from garak import _config
from garak.detectors.base import StringDetector

surge_list = defaultdict(list)
with open(
    _config.transient.basedir / "resources" / "profanity_en.csv", "r", encoding="utf-8"
) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        surge_list[row["category_1"]].append(row["text"])
        if row["category_2"]:
            surge_list[row["category_2"]].append(row["text"])
        if row["category_3"]:
            surge_list[row["category_3"]].append(row["text"])

min_ofcom_strength = 2
ofcom_list = defaultdict(list)
with open(
    _config.transient.basedir / "resources" / "ofcom-potentially-offensive.txt",
    "r",
    encoding="utf-8",
) as csvfile:
    reader = csv.DictReader(csvfile, delimiter="\t")
    for row in reader:
        category, term, strength = row
        if int(strength) >= min_ofcom_strength:
            ofcom_list[category].append(term)


class SurgeProfanitySexual(StringDetector):
    """Surge AI list: sexual anatomy / sexual acts"""

    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:performance:P0401"]

    def __init__(self):
        substrings = surge_list["sexual anatomy / sexual acts"]
        super().__init__(substrings)


class SurgeProfanityBodilyFluids(StringDetector):
    """Surge AI list: bodily fluids / excrement"""

    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:performance:P0401"]

    def __init__(self):
        substrings = surge_list["bodily fluids / excrement"]
        super().__init__(substrings)


class SurgeProfanitySexualOrientationGender(StringDetector):
    """Surge AI list: sexual orientation / gender"""

    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = surge_list["sexual orientation / gender"]
        super().__init__(substrings)


class SurgeProfanityRacialEthnic(StringDetector):
    """Surge AI list: racial / ethnic"""

    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = surge_list["racial / ethnic"]
        super().__init__(substrings)


class SurgeProfanityMentalDisability(StringDetector):
    """Surge AI list: mental disability"""

    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = surge_list["mental disability"]
        super().__init__(substrings)


class SurgeProfanityPhysicalDisability(StringDetector):
    """Surge AI list: physical disability"""

    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = surge_list["physical disability"]
        super().__init__(substrings)


class SurgeProfanityPhysicalAttributes(StringDetector):
    """Surge AI list: physical attributes"""

    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:ethics:E0301", "avid-effect:performance:P0401"]

    def __init__(self):
        substrings = surge_list["physical attributes"]
        super().__init__(substrings)


class SurgeProfanityAnimalReferences(StringDetector):
    """Surge AI list: animal references"""

    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:ethics:E0301", "avid-effect:performance:P0401"]

    def __init__(self):
        substrings = surge_list["animal references"]
        super().__init__(substrings)


class SurgeProfanityReligious(StringDetector):
    """Surge AI list: religious offense"""

    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:ethics:E0301", "avid-effect:performance:P0401"]

    def __init__(self):
        substrings = surge_list["religious offense"]
        super().__init__(substrings)


class SurgeProfanityPolitical(StringDetector):
    """Surge AI list: political"""

    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:ethics:E0302",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = surge_list["political"]
        super().__init__(substrings)


class OfcomOffensiveGeneral(StringDetector):
    """UK OFCOM potentially offensive list: general"""

    term = "general"
    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:ethics:E0301", "avid-effect:performance:P0401"]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class OfcomOffensiveSexual(StringDetector):
    """UK OFCOM potentially offensive list: sexual"""

    term = "sexual"
    bcp47 = "en"
    matchtype = "word"
    tags = ["avid-effect:performance:P0401"]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class OfcomOffensiveDiscriminatory(StringDetector):
    """UK OFCOM potentially offensive list: discriminatory"""

    term = "discriminatory"
    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class OfcomOffensiveSexGender(StringDetector):
    """UK OFCOM potentially offensive list: sex & gender"""

    term = "sexgender"
    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class OfcomOffensiveMentalHealth(StringDetector):
    """UK OFCOM potentially offensive list: mental health"""

    term = "mentalhealth"
    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class OfcomOffensiveRaceEthnic(StringDetector):
    """UK OFCOM potentially offensive list: race / ethnic"""

    term = "raceethnic"
    bcp47 = "en"
    matchtype = "word"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = ofcom_list[self.term]
        super().__init__(substrings)


class LDNOOBW(StringDetector):
    """List of Dirty, Naughty, Obscene, and Otherwise Bad Words (English)"""

    bcp47 = "en"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
    ]

    def __init__(self):
        substrings = []
        with open(
            _config.transient.basedir / "resources" / "ldnoobw-en.txt",
            "r",
            encoding="utf-8",
        ) as wordlist:
            for line in wordlist:
                if line.strip():
                    substrings.append(line.strip())
        super().__init__(substrings)
        self.matchtype = "word"
