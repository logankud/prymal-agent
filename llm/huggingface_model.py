from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class HFModel():

    def __init__(self, model_id, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
        self.model.to(device)
        self.device = device

    def __call__(self, prompt: str, **kwargs) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7
        )
        return self.tokenizer.decode(output[0], skip_special_tokens=True)