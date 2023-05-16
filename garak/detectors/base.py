#!/usr/bin/env python3

from colorama import Fore, Back, Style
import re

class Detector:
    def __init__(self):
        if not self.name:
            self.name = __class__ # short name
        self.description = "Empty detector"
        self.uri = "" # reference
        self.bcp47 = None # language this is for, in bcp47 format
        self.precision = 0.0
        self.recall = 0.0
        self.accuracy = None
        print(f'loading {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}detector{Style.RESET_ALL}: {self.name}')

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
        self.name = f"HF: {model_path}"
        super().__init__()

        self.detector_model_path = model_path
        self.detector_target_class = target_class
        
        self.detector_model = AutoModelForSequenceClassification.from_pretrained(self.detector_model_path)
        self.detector_tokenizer = AutoTokenizer.from_pretrained(self.detector_model_path)
        self.detector = TextClassificationPipeline(model=self.detector_model, tokenizer=self.detector_tokenizer)

        self.graceful_fail = False

    def detect(self, query):
        if isinstance(query, str):
            query = [query]
        if isinstance(query, list):
            try:
                detector_raw_results = self.detector(query, **self.tokenizer_kwargs)
            except Exception as e:
                if self.graceful_fail:
                    print(e)
                    return []
                else:
                    raise Exception() from e
        else:
            raise TypeError('Can only evaluate str or list')        
        
        detector_results = []
        for d in detector_raw_results:
            detector_results.append(
                (1-d['score'])/2 if d['label']!=self.detector_target_class else (1+d['score'])/2
                )

        return detector_results
    
class StringDetector(Detector):
    def __init__(self, substrings):
        super().__init__()
        self.substrings = substrings
        self.matchtype = "str" # str or word
    
    def detect(self, query):
        if isinstance(query, str):
            query = [query]
        if not isinstance(query, list):
            raise TypeError('Can only evaluate str or list')        

        detector_results = []
        for q in query:
            match = False
            for s in self.substrings:
                if self.matchtype == "str":
                    if s in q:
                        match = True
                elif self.matchtype == "word":
                    s = re.escape(s)
                    if re.search(f"\\b{s}\\b", q):
                        match = True
                else:
                    raise ValueError(f"Don't know how to process matchtype: {self.matchtype}")
            detector_results.append(1 if match else 0)

        return detector_results
