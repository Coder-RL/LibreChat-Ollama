"""
Preloads SentenceTransformer models required by the embedding pipeline.
Run once to avoid download stalls during tests or runtime.
"""

from sentence_transformers import SentenceTransformer

MODELS = [
    "all-mpnet-base-v2",
    "all-roberta-large-v1",
    "gtr-t5-xxl",  # This one is large (4GB+)
    "sentence-t5-xxl",  # Optional, also large
    # You can also mock/predefine a custom one if needed
]

print("📦 Preloading SentenceTransformer models...")

for model in MODELS:
    try:
        print(f"🔄 Loading: {model} ...")
        model_instance = SentenceTransformer(model)
        dim = model_instance.get_sentence_embedding_dimension()
        print(f"✅ Loaded '{model}' ({dim}D)")
    except Exception as e:
        print(f"❌ Failed to load model '{model}': {e}")

print("✅ All preload attempts complete.")
