from collections import defaultdict
import csv

from garak.detectors.base import StringDetector

surge_list = defaultdict(list)
with open("resources/profanity_en.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        surge_list[row["category_1"]] = row["text"]
        if row["category_2"]:
            surge_list[row["category_2"]] = row["text"]
        if row["category_3"]:
            surge_list[row["category_3"]] = row["text"]


class SurgeProfanityDetectorSexual(StringDetector):
    def __init__(self):
        self.name = "sexualterms"
        substrings = surge_list["sexual anatomy / sexual acts"]
        super().__init__(substrings)
        self.description = "Surge AI list: sexual anatomy / sexual acts"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorBodilyFluids(StringDetector):
    def __init__(self):
        self.name = "bodilyfluids"
        substrings = surge_list["bodily fluids / excrement"]
        super().__init__(substrings)
        self.description = "Surge AI list: bodily fluids / excrement"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorSexualOrientationGender(StringDetector):
    def __init__(self):
        self.name = "sexualorientationandgender"
        substrings = surge_list["sexual orientation / gender"]
        super().__init__(substrings)
        self.description = "Surge AI list: sexual orientation / gender"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorRacialEthnic(StringDetector):
    def __init__(self):
        self.name = "racialethnic"
        substrings = surge_list["racial / ethnic"]
        super().__init__(substrings)
        self.description = "Surge AI list: racial / ethnic"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorMentalDisability(StringDetector):
    def __init__(self):
        self.name = "mentaldisability"
        substrings = surge_list["mental disability"]
        super().__init__(substrings)
        self.description = "Surge AI list: mental disability"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorPhysicalDisability(StringDetector):
    def __init__(self):
        self.name = "physicaldisability"
        substrings = surge_list["physical disability"]
        super().__init__(substrings)
        self.description = "Surge AI list: physical disability"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorPhysicalAttributes(StringDetector):
    def __init__(self):
        self.name = "physicalattributes"
        substrings = surge_list["physical attributes"]
        super().__init__(substrings)
        self.description = "Surge AI list: physical attributes"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorAnimalReferences(StringDetector):
    def __init__(self):
        self.name = "animalreferences"
        substrings = surge_list["animal references"]
        super().__init__(substrings)
        self.description = "Surge AI list: animal references"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorReligious(StringDetector):
    def __init__(self):
        self.name = "religiousoffence"
        substrings = surge_list["religious offense"]
        super().__init__(substrings)
        self.description = "Surge AI list: religious offense"
        self.bcp47 = "en"
        self.matchtype = "word"


class SurgeProfanityDetectorPolitical(StringDetector):
    def __init__(self):
        self.name = "political"
        substrings = surge_list["political"]
        super().__init__(substrings)
        self.description = "Surge AI list: political"
        self.bcp47 = "en"
        self.matchtype = "word"
