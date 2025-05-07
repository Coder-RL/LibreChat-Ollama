# scripts/setup_environment.py

import os
from dotenv import load_dotenv

def ensure_directories():
    load_dotenv()
    model_cache = os.getenv("MODEL_CACHE_DIR")
    if model_cache:
        os.makedirs(model_cache, exist_ok=True)
        print(f"✅ Created or verified model cache directory: {model_cache}")
    else:
        print("⚠️ MODEL_CACHE_DIR is not set in .env")

if __name__ == "__main__":
    ensure_directories()
