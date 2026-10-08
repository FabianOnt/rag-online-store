from pydantic import BaseModel

class TextEmbeddingResponse(BaseModel):
    chunks: list[str]
    embeddings: list[list[float]]

class TextEmbeddingRequest(BaseModel):
    text: str