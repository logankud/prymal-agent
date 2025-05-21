from transformers import pipeline
from huggingface_hub import login
import os

class HFTextGenModel:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.2"):
        # Login to Hugging Face Hub
        login(token=os.environ["HUGGING_FACE_TOKEN"])
        # Load the model into a text generation pipeline
        self.pipeline = pipeline("text-generation", model=model_name)
        
    def run(self, prompt: str) -> str:
        """Function to invoke the text generation pipeline to generate text response to an input prompt"""

        
        result = self.pipeline(prompt, max_new_tokens=200, do_sample=True)
        return result[0]["generated_text"]

    def __call__(self, prompt: str, tools_to_call_from=None, tool_choice=None, **kwargs) -> str:
        return self.run(prompt)
