import os

from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer


TOKENIZER_MODEL = os.getenv("TOKENIZER_MODEL")
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL")

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
embedder = SentenceTransformer(EMBEDDINGS_MODEL)