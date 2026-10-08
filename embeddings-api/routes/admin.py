from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import verify_admin_key
from schemas.admin import TextEmbeddingResponse, TextEmbeddingRequest
from services.embeddings.core import text_splitter, embedder

router = APIRouter(
    prefix="/admin",
    tags=["Unlimited rate functions"],
    dependencies=[Depends(verify_admin_key)]
)

@router.post("/embedd", status_code=status.HTTP_201_CREATED)
def embedd(payload: TextEmbeddingRequest):
    try:
        chunks = text_splitter.split_text(payload.text)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text chunks could be generated from the document."
            )
    
        embeddings = embedder.encode(chunks)
    
        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()

        return TextEmbeddingResponse(
            chunks=chunks,
            embeddings=embeddings
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))