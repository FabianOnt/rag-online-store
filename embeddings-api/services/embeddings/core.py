import os

from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

TOKENIZER_MODEL = os.getenv("TOKENIZER_MODEL")
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL")


tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL, local_files_only=True)
embedder = SentenceTransformer(EMBEDDINGS_MODEL, local_files_only=True)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=lambda text: len(tokenizer.encode(text))
)