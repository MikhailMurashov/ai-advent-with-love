import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "")
API_KEY = os.getenv("API_KEY", "")

MODELS = {
    "Llama-3.2-1B": "huggingface/meta-llama/Llama-3.2-1B-Instruct",
    "Llama-3.1-8B": "huggingface/meta-llama/Llama-3.1-8B-Instruct",
    "Llama-4-Scout-17B": "huggingface/meta-llama/Llama-4-Scout-17B-16E-Instruct",
}
