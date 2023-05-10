#!/usr/bin/env python3

from transformers import pipeline

class HFBaseModel:
    def __init__(self, name, do_sample=True, num_return_sequences=10):
        self.generator = pipeline(
            'text-generation', 
            model=name, 
            do_sample=do_sample,
            num_return_sequences=num_return_sequences)

    def generate(self, prompt):
        raw_output = self.generator(prompt)
        return [i['generated_text'] for i in raw_output]

class PersuaderModule:
    def __init__(self):
        self.description = "Empty Persuader module"
        self.precision = 0.0
        self.recall = 0.0
        self.accuracy = None
        self.lang = None #bcp47
        pass
    
    def probe(self, target):
        # attempt to exploit the target, return list of results
        return []

class PersuaderDetector:
    def __init__(self):
        self.description = "Empty Persuader detector"
        self.lang = None #bcp47

    def detect(self, query):
        if isinstance(query, str):
            query = [query]
        if isinstance(query, list):
            yield None
        else:
            raise TypeError('Can only evaluate str or list')

class PersuaderHFDetector(PersuaderDetector):

    def __init__(self, model_path, target_class):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, TextClassificationPipeline
        super().__init__()

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