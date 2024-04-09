"""LLaVa Generator"""

from typing import List
from garak.generators.base import Generator

from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch
from PIL import Image
import requests

class LLaVA(Generator):
    """Get LLaVA ([ text + image ] -> text) generations"""

    # "exist_tokens + max_new_tokens < 4K is the golden rule."
    # https://github.com/haotian-liu/LLaVA/issues/1095#:~:text=Conceptually%2C%20as%20long%20as%20the%20total%20tokens%20are%20within%204K%2C%20it%20would%20be%20fine%2C%20so%20exist_tokens%20%2B%20max_new_tokens%20%3C%204K%20is%20the%20golden%20rule.
    max_tokens = 4000
    
    def __init__(self, name="", generations=10):
        self.processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf")
        self.model = LlavaNextForConditionalGeneration.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf", torch_dtype=torch.float16, low_cpu_mem_usage=True) 
        self.model.to("cuda:0")
        
    def generate(self, prompt: str) -> List[str]:
        text_prompt = prompt[0]
        image_prompt = Image.open(prompt[1])


        inputs = self.processor(text_prompt, image_prompt, return_tensors="pt").to("cuda:0")

        # autoregressively complete prompt
        output = self.model.generate(**inputs, max_new_tokens = self.max_tokens)

        output = self.processor.decode(output[0], skip_special_tokens=True)
        
        return [output]

default_class = "LLaVA"