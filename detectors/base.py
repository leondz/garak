#!/usr/bin/env python3

from colorama import Fore, Back, Style

class Detector:
    def __init__(self):
        self.name = "" # short name
        self.description = "Empty detector"
        self.uri = "" # reference
        self.bcp47 = None # language this is for, in bcp47 format
        self.precision = 0.0
        self.recall = 0.0
        self.accuracy = None


    def detect(self, query):
        if isinstance(query, str):
            query = [query]
        if isinstance(query, list):
            yield None
        else:
            raise TypeError('Can only evaluate str or list')

class HFDetector(Detector):

    def __init__(self, model_path, target_class):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, TextClassificationPipeline
        super().__init__()

        print('loading '+Style.RESET_ALL+Fore.LIGHTBLUE_EX+'detector'+Style.RESET_ALL+': HF', model_path)

        self.detector_model_path = model_path
        self.detector_target_class = target_class

        self.detector_model = AutoModelForSequenceClassification.from_pretrained(self.detector_model_path)
        self.detector_tokenizer = AutoTokenizer.from_pretrained(self.detector_model_path)
        self.detector = TextClassificationPipeline(model=self.detector_model, tokenizer=self.detector_tokenizer)

    def detect(self, query):
        if isinstance(query, str):
            query = [query]
        if isinstance(query, list):
            detector_raw_results = self.detector(query)
        else:
            raise TypeError('Can only evaluate str or list')        
        
        detector_results = []
        for d in detector_raw_results:
            detector_results.append(
                (1-d['score'])/2 if d['label']!=self.detector_target_class else (1+d['score'])/2
                )

        return detector_results