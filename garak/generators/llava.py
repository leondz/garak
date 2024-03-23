"""LLaVa Generator"""

from typing import List
from garak.generators.base import Generator

from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch
from PIL import Image
import requests

class LLaVA(Generator):
    """Get LLaVA ([ text + image ] -> text) generations"""
    
    def __init__(self, name="", generations=10):
        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
        self.processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf", proxies = proxies)
        self.model = LlavaNextForConditionalGeneration.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf", torch_dtype=torch.float16, low_cpu_mem_usage=True, proxies = proxies) 
        self.model.to("cuda:0")
        
    def generate(self, prompt: str) -> List[str]:
        # prepare image and text prompt, using the appropriate prompt template
        url = "https://github.com/haotian-liu/LLaVA/blob/1a91fc274d7c35a9b50b3cb29c4247ae5837ce39/images/llava_v1_5_radar.jpg?raw=true"
        image = Image.open(requests.get(url, stream=True).raw)
        prompt = "[INST] <image>\nWhat is shown in this image? [/INST]"

        inputs = self.processor(prompt, image, return_tensors="pt").to("cuda:0")

        # autoregressively complete prompt
        output = self.model.generate(**inputs, max_new_tokens=100)

        output = self.processor.decode(output[0], skip_special_tokens=True)
        
        return [output]

default_class = "LLaVA"