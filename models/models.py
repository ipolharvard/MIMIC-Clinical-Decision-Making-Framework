import os
from os.path import join
from typing import Any, List, Mapping, Dict

import torch
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
from transformers import GenerationConfig, StoppingCriteriaList
from auto_gptq import exllama_set_max_input_length
from langchain.llms.base import LLM
from exllamav2.generator import ExLlamaV2Sampler
import tiktoken

from models.utils import create_stop_criteria, create_stop_criteria_exllama
from agents.agent import STOP_WORDS
from utils.nlp import extract_sections


class CustomLLM(LLM):
    model_name: str
    max_context_length: int
    probabilities: torch.Tensor = None
    exllama: bool = False
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    truncation_side: str = "left"
    model: Any
    generator: Any
    tokenizer: Any
    seed: int
    self_consistency: bool = False

    openai_api_key: str = None
    openai_api_base: str = None
    tags: Dict[str, str] = None

    @property
    def _llm_type(self) -> Any:
        return "custom"

    @property
    def _llm_name(self) -> str:
        return self.model_name

    @property
    def _llm_device(self) -> str:
        return self.model.device

    @property
    def _llm_8bit(self) -> bool:
        return self.load_in_8bit

    @property
    def _llm_4bit(self) -> bool:
        return self.load_in_4bit

    @property
    def _llm_truncation_side(self) -> str:
        return self.truncation_side

    def load_model(self, base_models: str) -> None:
        torch.cuda.empty_cache()

        if self.model_name == "Human":
            return

        elif self.model_name in ["gpt-3.5-turbo", "gpt-4"]:
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
            return

        elif "ollama" in self.model_name:
            print("Using ollama")
            from transformers import AutoTokenizer

            print(f"{self.tokenizer=}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer)

            self.model_name = self.model_name.replace("ollama-", "")

            print(f"{self.model_name=}")

            return

        elif self.model_name == "Meta-Llama-3-70B-Instruct-GGUF":
            from transformers import AutoTokenizer

            print(f"{self.tokenizer=}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer)

            print(f"{self.model_name=}")

            return

        elif self.model_name == "Meta-Llama-3-70B-Instruct":
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
            return

        elif "GPTQ" in self.model_name:
            if self.exllama:
                from exllamav2 import ExLlamaV2Cache
                from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Tokenizer
                from models.exllamav2_generator_base_custom import (
                    ExLlamaV2BaseGenerator,
                )

                torch.cuda._lazy_init()
                config = ExLlamaV2Config()
                config.model_dir = join(base_models, self.model_name)
                config.prepare()
                config.max_seq_len = self.max_context_length
                config.scale_pos_emb = 1.0
                config.scale_alpha_value = 1.0
                config.no_flash_attn = False
                self.model = ExLlamaV2(config)
                self.model.load()
                self.tokenizer = ExLlamaV2Tokenizer(config)
                cache = ExLlamaV2Cache(self.model)
                self.generator = ExLlamaV2BaseGenerator(self.model, cache, self.tokenizer)
                self.generator.warmup()

            else:
                # from transformers import LlamaTokenizer, LlamaForCausalLM

                # base_model = join(base_models, self.model_name)

                # self.tokenizer = LlamaTokenizer.from_pretrained(base_model)
                # self.model = LlamaForCausalLM.from_pretrained(
                #     base_model,
                #     torch_dtype=torch.float16,
                #     device_map="auto",
                # )
                # self.model = exllama_set_max_input_length(self.model, self.max_context_length)

                from transformers import AutoModelForCausalLM, AutoTokenizer

                print("Using AutoTokenizer and AutoModelForCausalLM")

                base_model = join(base_models, self.model_name)

                self.tokenizer = AutoTokenizer.from_pretrained(base_model)
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    device_map="auto",
                )

        self.tokenizer.truncation_side = "left"

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(10))
    def completion_with_backoff(self, **kwargs):
        return openai.ChatCompletion.create(**kwargs)

    def remove_input_tokens(self, output_tokens, ids):
        # Truncate the larger tensor to match the size of the smaller one
        min_size = min(output_tokens.size(1), ids.size(1))
        truncated_output_tokens = output_tokens[:, :min_size]
        truncated_ids = ids[:, :min_size]

        # Element-wise comparison and cumulative product to count length of common prefix
        common_prefix = (truncated_output_tokens == truncated_ids).cumprod(dim=0).sum().item()

        return output_tokens[:, common_prefix:]

    def _call(
        self,
        prompt: str,
        stop: List[str],
        do_sample=True,
        temperature=0.01,
        top_k=1,
        top_p=0.95,
        num_beams=1,
        repetition_penalty=1.2,
        length_penalty=1.0,
        **kwargs,
    ) -> str:
        self.probabilities = None

        if self.model_name == "Human":
            output = input(prompt)

        elif self.openai_api_key:
            from openai import OpenAI

            messages = extract_sections(
                prompt,
                self.tags,
            )

            # response = self.completion_with_backoff(
            #     model=self.model_name,
            #     messages=messages,
            #     stop=STOP_WORDS,
            #     temperature=0.0,
            #     seed=self.seed,
            # )
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_api_base,
            )
            completion = client.chat.completions.create(
                messages=messages,
                model=self.model_name,
            )

            output = completion.choices[0].message.content

        elif self.exllama:
            with torch.inference_mode():
                ids = self.tokenizer.encode(prompt, encode_special_tokens=True)
                tokens_prompt = ids.shape[-1]

                settings = ExLlamaV2Sampler.Settings()
                if self.self_consistency:
                    settings = settings.clone()
                    settings.temperature = 0.7
                    seed = None
                else:
                    settings = settings.greedy_clone()
                    seed = self.seed

                stop_criteria = create_stop_criteria_exllama(stop, self.tokenizer.eos_token_id, self.tokenizer)

                output_tokens, self.probabilities = self.generator.generate_simple(
                    prompt,
                    gen_settings=settings,
                    num_tokens=self.max_context_length - tokens_prompt,
                    seed=seed,
                    token_healing=True,
                    encode_special_tokens=True,
                    decode_special_tokens=False,
                    stop_criteria=stop_criteria,
                )

                output_tokens = self.remove_input_tokens(output_tokens, ids)
                output = self.tokenizer.decode(output_tokens, decode_special_tokens=False)[0]
        else:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=self.max_context_length,
                truncation=True,
                padding=False,
            )
            input_ids = inputs["input_ids"].to(self.model.device)

            generation_config = GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                num_beams=num_beams,
                do_sample=do_sample,
                repetition_penalty=repetition_penalty,
                length_penalty=length_penalty,
                **kwargs,
            )

            stop_criteria = create_stop_criteria(stop, self.tokenizer, self.model.device)

            with torch.no_grad():
                generation_output = self.model.generate(
                    input_ids=input_ids,
                    generation_config=generation_config,
                    stopping_criteria=StoppingCriteriaList([stop_criteria]),
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_length=self.max_context_length,
                )

            s = generation_output.sequences
            s_no_input = s[:, input_ids.shape[1] :]
            output = self.tokenizer.batch_decode(s_no_input, skip_special_tokens=True)[0]

        # Remove observations strings from output if generated
        for stop_word in STOP_WORDS + stop:
            output = output.replace(stop_word, "")

        return output.strip()

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "load_in_8bit": self.load_in_8bit,
            "load_in_4bit": self.load_in_4bit,
        }
