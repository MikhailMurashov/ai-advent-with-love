import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "")
API_KEY = os.getenv("API_KEY", "")
