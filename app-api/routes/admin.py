from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session

from services.store_db.session import get_db as get_store_db
from services.store_db.crud import create_category, create_product, create_document_chunk
from schemas.admin import CategoryCreate, ProductCreate, DocumentUploadResponse
from dependencies import verify_admin_key

from services.embeddings.tools import get_embedding

router = APIRouter(
    prefix="/admin",
    tags=["Admin level functions"],
    dependencies=[Depends(verify_admin_key)]
)

@router.post("/categories", status_code=status.HTTP_201_CREATED)
def add_category(category_in: CategoryCreate, db: Session = Depends(get_store_db)):
    try:
        return create_category(db=db, name=category_in.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/products", status_code=status.HTTP_201_CREATED)
def add_product(product_in: ProductCreate, db: Session = Depends(get_store_db)):
    try:
        return create_product(
            db=db,
            name=product_in.name,
            price=product_in.price,
            category_name=product_in.category_name,
            units=product_in.units,
            discount=product_in.discount,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/upload-document", 
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentUploadResponse
)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    product_sku: str = Form(...),
    db: Session = Depends(get_store_db)
):

    try:
        content_bytes = await file.read()
        doc_text = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file as text: {str(e)}"
        )

    if not doc_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Uploaded file is empty."
        )

    chunks, vectors = get_embedding(doc_text)

    created_count = 0
    try:
        for i, (chunk, embedding) in enumerate(zip(chunks, vectors)):
            create_document_chunk(
                db=db,
                file_name=file.filename,
                doc_type=doc_type,
                chunk_index=i,
                chunk_text=chunk,
                embedding=embedding,
                product_sku=product_sku,
            )
            created_count += 1
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))

    return DocumentUploadResponse(
        file_name=file.filename,
        chunks_created=created_count,
        product_sku=product_sku
    )