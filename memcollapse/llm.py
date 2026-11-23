"""Thin batched HuggingFace wrapper: greedy generation + multiple-choice letter scoring."""
from __future__ import annotations

import logging

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .prompts import LETTERS

log = logging.getLogger(__name__)


class HFModel:
    def __init__(self, name: str, dtype: torch.dtype = torch.bfloat16, device: str = "cuda"):
        self.name = name
        self.tok = AutoTokenizer.from_pretrained(name)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype, device_map=device)
        self.model.eval()
        self.letter_ids = [self._single_token_id(L) for L in LETTERS]

    def _single_token_id(self, letter: str) -> int:
        ids = self.tok.encode(letter, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError(f"letter {letter!r} is not a single token for {self.name}: {ids}")
        return ids[0]

    def _encode(self, batch_messages: list[list[dict]]) -> dict:
        texts = [self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                 for m in batch_messages]
        enc = self.tok(texts, return_tensors="pt", padding=True, add_special_tokens=False)
        return {k: v.to(self.model.device) for k, v in enc.items()}

    @torch.inference_mode()
    def generate(self, batch_messages: list[list[dict]], max_new_tokens: int,
                 batch_size: int = 16) -> list[str]:
        outs: list[str] = []
        for i in range(0, len(batch_messages), batch_size):
            enc = self._encode(batch_messages[i:i + batch_size])
            gen = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                      pad_token_id=self.tok.pad_token_id)
            new = gen[:, enc["input_ids"].shape[1]:]
            outs += [t.strip() for t in self.tok.batch_decode(new, skip_special_tokens=True)]
        return outs

    @torch.inference_mode()
    def choice_logprobs(self, batch_messages: list[list[dict]],
                        batch_size: int = 16) -> list[list[float]]:
        """Log-probabilities (renormalised over A-D) of the first answer token."""
        res: list[list[float]] = []
        for i in range(0, len(batch_messages), batch_size):
            enc = self._encode(batch_messages[i:i + batch_size])
            logits = self.model(**enc).logits[:, -1, :].float()
            sub = torch.log_softmax(logits[:, self.letter_ids], dim=-1)
            res += sub.cpu().tolist()
        return res
