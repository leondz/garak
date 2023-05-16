#!/usr/bin/env python3

from colorama import Fore, Back, Style
import re
from transformers import pipeline
import warnings

class HFBaseGenerator:
    def __init__(self, name, do_sample=True, num_return_sequences=10):
        self.fullname, self.name = name, name.split('/')[-1]
        print(f'loading {Style.RESET_ALL}{Fore.LIGHTMAGENTA_EX} generator {Style.RESET_ALL}: HF {name}')
        self.generator = pipeline(
            'text-generation', 
            model=name, 
            do_sample=do_sample,
            num_return_sequences=num_return_sequences,
            )
        self.deprefix_prompt = False

    def generate(self, prompt):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            try:
                raw_output = self.generator(
                    prompt,
                    pad_token_id = self.generator.tokenizer.eos_token_id,
                    max_new_tokens = 512,
                    #max_length = 1024,
                    )
            except:
                raw_output = [] # could handle better than this..
        generations = [i['generated_text'] for i in raw_output] # generator returns 10 outputs by default in __init__
        if not self.deprefix_prompt:
            return generations
        else:
            return [re.sub("^" + re.escape(prompt), '', i) for i in generations]
