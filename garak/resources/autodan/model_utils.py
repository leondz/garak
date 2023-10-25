import gc
import torch
from fastchat.conversation import Conversation
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import fastchat.model as fsmodel
from logging import getLogger
from typing import Tuple

logger = getLogger(__name__)


def generate(model, tokenizer, input_ids, assistant_role_slice, gen_config=None):
    """
    Generate output from specified model

    Args:
        model (torch.nn.Model): model to generate from
        tokenizer (PreTrainedTokenizer): Tokenizer for the specified model
        input_ids (torch.Tensor): Tokenized inputs to the model
        assistant_role_slice ():
        gen_config (transformers.GenerationConfig): Generation configuration

    Returns:

    """
    if gen_config is None:
        gen_config = model.generation_config
        gen_config.max_new_tokens = 64
    input_ids = input_ids[:assistant_role_slice.stop].to(model.device).unsqueeze(0)
    attn_masks = torch.ones_like(input_ids).to(model.device)
    output_ids = model.generate(input_ids,
                                attention_mask=attn_masks,
                                generation_config=gen_config,
                                pad_token_id=tokenizer.pad_token_id)[0]
    return output_ids[assistant_role_slice.stop:]


def check_for_attack_success(model, tokenizer, input_ids, assistant_role_slice, test_prefixes, gen_config=None) -> Tuple[bool, str]:
    """
    Check if the jailbreak is successful against the specified model

    Args:
        model (transformers.PreTrainedModel): Model for evaluation
        tokenizer (transformers.PreTrainedTokenizer): Tokenizer associated with model
        input_ids (torch.Tensor): Tokenized inputs
        assistant_role_slice ():
        test_prefixes (list): List of test prefixes
        gen_config (transformers.GenerationConfig):

    Returns:
        Tuple:
            Boolean of whether the model jailbreak was successful
            Generated string
    """
    jailbreak = False
    gen_str = tokenizer.decode(generate(model,
                                        tokenizer,
                                        input_ids,
                                        assistant_role_slice,
                                        gen_config=gen_config)).strip()
    uppercase_test_prefixes = [word.upper() for word in test_prefixes]
    if len(gen_str) != 0 and not gen_str.isupper():
        jailbreak = not any([prefix in gen_str for prefix in test_prefixes+uppercase_test_prefixes])
    return jailbreak, gen_str


def forward(*, model, input_ids, attention_mask, batch_size=512) -> torch.Tensor:
    """
    Run a forward pass on the specified model
    Args:
        model (torch.nn.Model): Model to run the forward pass on
        input_ids (torch.Tensor): Tokenized input to the model
        attention_mask (torch.Tensor): Attention mask from tokenizer
        batch_size (int): Number of samples to run

    Returns:
        Tensor of logits
    """
    logits = []
    for i in range(0, input_ids.shape[0], batch_size):

        batch_input_ids = input_ids[i:i + batch_size]
        if attention_mask is not None:
            batch_attention_mask = attention_mask[i:i + batch_size]
        else:
            batch_attention_mask = None

        logits.append(model(input_ids=batch_input_ids, attention_mask=batch_attention_mask).logits)

        # Do we need to do garbage collection here?
        gc.collect()

    # Does this do anything since we return from the scope after this call?
    del batch_input_ids, batch_attention_mask

    return torch.cat(logits, dim=0)


def load_model_and_tokenizer(model_path: str, tokenizer_path=None, device='cuda:0', **kwargs):
    """
    Loads model and tokenizer from specified model path
    Args:
        model_path (str): Path to model (and tokenizer file, if not specified)
        tokenizer_path (str): Path to tokenizer (OPTIONAL)
        device (str): What device to run the model on.
        **kwargs (dict): Additional keyword arguments to pass to the model loader.

    Returns:

    """
    # TODO: Is `trust_remote_code=True` a safe default?
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True,
                                                 **kwargs).to(device).eval()

    tokenizer_path = model_path if tokenizer_path is None else tokenizer_path

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True, use_fast=False)

    # Modify tokenizer token ids and padding for compatibility.
    if 'oasst-sft-6-llama-30b' in tokenizer_path:
        tokenizer.bos_token_id = 1
        tokenizer.unk_token_id = 0
    if 'guanaco' in tokenizer_path:
        tokenizer.eos_token_id = 2
        tokenizer.unk_token_id = 0
    if 'llama-2' in tokenizer_path:
        tokenizer.pad_token = tokenizer.unk_token
        tokenizer.padding_side = 'left'
    if 'falcon' in tokenizer_path:
        tokenizer.padding_side = 'left'
    if not tokenizer.pad_token:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def download_models(model_name: str, base_model_path: str):
    """
    Loads and saves specified pretrained huggingface model to `base_model_path`

    Args:
        model_name (str): Huggingface model name
        base_model_path (str): Path to save model and tokenizer

    Returns:
        None
    """
    Path(base_model_path).mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(model_name,
                                                 device_map='auto',
                                                 torch_dtype=torch.float16,
                                                 low_cpu_mem_usage=True, use_cache=False)
    # Save the model and the tokenizer
    model.save_pretrained(base_model_path, from_pt=True)
    tokenizer.save_pretrained(base_model_path, from_pt=True)


def load_conversation_template(template_name: str):
    """
    Load the specified conversation template
    Args:
        template_name (str): template name to load from fastchat

    Returns:
        Conversation template
    """
    try:
        conv_template = fsmodel.get_conversation_template(template_name)
        if conv_template.name == 'zero_shot':
            conv_template.roles = tuple(['### ' + r for r in conv_template.roles])
            conv_template.sep = '\n'
        elif conv_template.name == 'llama-2':
            conv_template.sep2 = conv_template.sep2.strip()
        return conv_template
    except Exception as e:
        logger.error(e)


class AutoDanPrefixManager:
    def __init__(self, *, tokenizer, conv_template, instruction, target, adv_string):
        """
        Prefix manager class for AutoDAN
        Args:
            tokenizer (PreTrainedTokenizer): Tokenizer for model
            conv_template (ConversationTemplate): Conversation template for specified model
            instruction (str): Instruction to pass to the model
            target (str): Target output string
            adv_string (str): Adversarial (jailbreak) string
        """

        self.tokenizer = tokenizer
        self.conv_template = conv_template
        self.instruction = instruction
        self.target = target
        self.adv_string = adv_string

    def get_prompt(self, adv_string=None):

        if adv_string is not None:
            self.adv_string = adv_string

        self.conv_template.append_message(self.conv_template.roles[0], f"{self.adv_string} {self.instruction} ")
        self.conv_template.append_message(self.conv_template.roles[1], f"{self.target}")
        prompt = self.conv_template.get_prompt()

        encoding = self.tokenizer(prompt)
        toks = encoding.input_ids

        if self.conv_template.name == 'llama-2':
            self.conv_template.messages = []

            self.conv_template.append_message(self.conv_template.roles[0], None)
            toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
            self._user_role_slice = slice(None, len(toks))

            self.conv_template.update_last_message(f"{self.instruction}")
            toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
            self._goal_slice = slice(self._user_role_slice.stop, max(self._user_role_slice.stop, len(toks)))

            separator = ' ' if self.instruction else ''
            self.conv_template.update_last_message(f"{self.adv_string}{separator}{self.instruction}")
            toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
            self._control_slice = slice(self._goal_slice.stop, len(toks))

            self.conv_template.append_message(self.conv_template.roles[1], None)
            toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
            self._assistant_role_slice = slice(self._control_slice.stop, len(toks))

            self.conv_template.update_last_message(f"{self.target}")
            toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
            self._target_slice = slice(self._assistant_role_slice.stop, len(toks) - 2)
            self._loss_slice = slice(self._assistant_role_slice.stop - 1, len(toks) - 3)

        else:
            python_tokenizer = False or self.conv_template.name == 'oasst_pythia'
            try:
                encoding.char_to_token(len(prompt) - 1)
            except:
                python_tokenizer = True

            if python_tokenizer:
                # This is specific to the vicuna and pythia tokenizer and conversation prompt.
                # It will not work with other tokenizers or prompts.
                self.conv_template.messages = []

                self.conv_template.append_message(self.conv_template.roles[0], None)
                toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
                self._user_role_slice = slice(None, len(toks))

                self.conv_template.update_last_message(f"{self.instruction}")
                toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
                self._goal_slice = slice(self._user_role_slice.stop, max(self._user_role_slice.stop, len(toks) - 1))

                separator = ' ' if self.instruction else ''
                self.conv_template.update_last_message(f"{self.adv_string}{separator}{self.instruction}")
                toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
                self._control_slice = slice(self._goal_slice.stop, len(toks) - 1)

                self.conv_template.append_message(self.conv_template.roles[1], None)
                toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
                self._assistant_role_slice = slice(self._control_slice.stop, len(toks))

                self.conv_template.update_last_message(f"{self.target}")
                toks = self.tokenizer(self.conv_template.get_prompt()).input_ids
                self._target_slice = slice(self._assistant_role_slice.stop, len(toks) - 1)
                self._loss_slice = slice(self._assistant_role_slice.stop - 1, len(toks) - 2)
            else:
                self._system_slice = slice(
                    None,
                    encoding.char_to_token(len(self.conv_template.system))
                )
                self._user_role_slice = slice(
                    encoding.char_to_token(prompt.find(self.conv_template.roles[0])),
                    encoding.char_to_token(
                        prompt.find(self.conv_template.roles[0]) + len(self.conv_template.roles[0]) + 1)
                )
                self._goal_slice = slice(
                    encoding.char_to_token(prompt.find(self.instruction)),
                    encoding.char_to_token(prompt.find(self.instruction) + len(self.instruction))
                )
                self._control_slice = slice(
                    encoding.char_to_token(prompt.find(self.adv_string)),
                    encoding.char_to_token(prompt.find(self.adv_string) + len(self.adv_string))
                )
                self._assistant_role_slice = slice(
                    encoding.char_to_token(prompt.find(self.conv_template.roles[1])),
                    encoding.char_to_token(
                        prompt.find(self.conv_template.roles[1]) + len(self.conv_template.roles[1]) + 1)
                )
                self._target_slice = slice(
                    encoding.char_to_token(prompt.find(self.target)),
                    encoding.char_to_token(prompt.find(self.target) + len(self.target))
                )
                self._loss_slice = slice(
                    encoding.char_to_token(prompt.find(self.target)) - 1,
                    encoding.char_to_token(prompt.find(self.target) + len(self.target)) - 1
                )

        self.conv_template.messages = []

        return prompt

    def get_input_ids(self, adv_string=None):
        """
        Get input ids from the tokenizer for a provided string
        Args:
            adv_string (str): String to tokenize

        Returns:
            Torch tensor of input_ids
        """
        prompt = self.get_prompt(adv_string=adv_string)
        toks = self.tokenizer(prompt).input_ids
        input_ids = torch.tensor(toks[:self._target_slice.stop])

        return input_ids
