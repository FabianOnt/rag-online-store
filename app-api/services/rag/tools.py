import json
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from sqlalchemy import select, or_

from services.store_db.models import ProductSummary, DocumentSearch, ReviewsSearch
from services.store_db.session import get_db as get_store_db

from services.embeddings.tools import get_embedding

class VectorSearchInput(BaseModel):
    query: str = Field(description="Semantic search query describing product needs, features, or questions.")
    search_descriptions: bool = Field(default=True, description="Search product descriptions and technical specifications.")
    search_faqs: bool = Field(default=False, description="Include product-related FAQs in search.")
    search_warranty: bool = Field(default=False, description="Include warranty documents in search.")
    limit: int = Field(default=5, description="Number of items to retrieve.")

@tool(args_schema=VectorSearchInput)
def vector_search(query: str, search_descriptions: bool = True, search_faqs: bool = False, search_warranty: bool = False, limit: int = 5) -> str:
    """Finds products matching a semantic query using vector similarity search."""
    chunks, vectors = get_embedding(query)
    query_vector = vectors[0]
    
    filters = []
    if search_descriptions:
        filters.append(DocumentSearch.file_name.ilike("%desc%") | DocumentSearch.file_name.ilike("%spec%"))
    if search_faqs:
        filters.append(DocumentSearch.file_name.ilike("%faq%"))
    if search_warranty:
        filters.append(DocumentSearch.file_name.ilike("%warranty%"))

    db = next(get_store_db())
    try:
        stmt = select(
            DocumentSearch.sku,
            DocumentSearch.file_name,
            DocumentSearch.chunk_text,
            DocumentSearch.embedding.cosine_distance(query_vector).label("distance")
        )
        
        if filters:
            stmt = stmt.where(or_(*filters))
            
        stmt = stmt.order_by("distance").limit(limit)
        results = db.execute(stmt).all()

        if not results:
            return "No matching document chunks found."

        output = []
        for row in results:
            output.append({
                "sku": row.sku,
                "file_name": row.file_name,
                "chunk": row.chunk_text,
                "similarity_score": round(1 - float(row.distance), 4)
            })
        
        return json.dumps(output, indent=2)
    finally: db.close()



class ProductNameSearchInput(BaseModel):
    product_name: str = Field(description="The product name.")

@tool(args_schema=ProductNameSearchInput)
def product_search_name(product_name: str) -> str:
    """Retrieves product SKU via exact or ILIKE SQL matching, falling back to vector search if no direct match is found."""
    db = next(get_store_db())
    try:
        stmt = select(ProductSummary).where(
            ProductSummary.product_name.ilike(f"%{product_name}%")
        ).limit(5)
        
        products = db.scalars(stmt).all()

        if products:
            res = [{
                "sku": p.sku,
                "product_name": p.product_name,
                "final_price": float(p.final_price),
                "category": p.category,
                "avg_rating": float(p.avg_rating)
            } for p in products]
            return json.dumps({"match_type": "sql_like", "results": res}, indent=2)
    finally:
        db.close()

    chunks, vectors = get_embedding(product_name)
    query_vector = vectors[0]
    db = next(get_store_db())
    try:
        stmt = select(
            DocumentSearch.sku,
            DocumentSearch.chunk_text,
            DocumentSearch.embedding.cosine_distance(query_vector).label("distance")
        ).order_by("distance").limit(3)

        results = db.execute(stmt).all()
        if not results:
            return f"No products found matching name '{product_name}'."

        res = [{"sku": row.sku, "snippet": row.chunk_text, "score": round(1 - float(row.distance), 4)} for row in results]
        return json.dumps({"match_type": "vector_fallback", "results": res}, indent=2)
    finally:
        db.close()


class ProductSearchInput(BaseModel):
    product_sku: str = Field(description="The unique product SKU identifier.")
    include_faqs: bool = Field(default=False, description="Set to true if user question involves troubleshooting or usage.")

@tool(args_schema=ProductSearchInput)
def product_search(product_sku: str, include_faqs: bool = False) -> str:
    """Retrieves exact metadata (price, specs, category, rating) for a specific product SKU."""
    db = next(get_store_db())
    try:
        product = db.scalars(
            select(ProductSummary).where(ProductSummary.sku == product_sku)
        ).first()

        if not product:
            return f"Product with SKU '{product_sku}' not found."

        data = {
            "sku": product.sku,
            "product_name": product.product_name,
            "original_price": float(product.original_price),
            "discount": float(product.discount),
            "final_price": float(product.final_price),
            "available_units": product.available_units,
            "category": product.category,
            "review_count": product.review_count,
            "avg_rating": float(product.avg_rating)
        }

        if include_faqs:
            faq_chunks = db.scalars(
                select(DocumentSearch.chunk_text).where(
                    DocumentSearch.sku == product_sku,
                    DocumentSearch.file_name.ilike("%faq%")
                )
            ).all()
            data["faqs"] = faq_chunks if faq_chunks else ["No FAQs found for this product."]

        return json.dumps(data, indent=2)
    finally:
        db.close()


@tool
def product_search_reviews(product_sku: str) -> str:
    """Retrieves top 6 positive and bottom 6 negative reviews with comments for a specific SKU."""
    db = next(get_store_db())
    try:
        top_reviews = db.scalars(
            select(ReviewsSearch)
            .where(ReviewsSearch.sku == product_sku, ReviewsSearch.comment.isnot(None))
            .order_by(ReviewsSearch.rating.desc())
            .limit(6)
        ).all()

        bottom_reviews = db.scalars(
            select(ReviewsSearch)
            .where(ReviewsSearch.sku == product_sku, ReviewsSearch.comment.isnot(None))
            .order_by(ReviewsSearch.rating.asc())
            .limit(6)
        ).all()

        if not top_reviews and not bottom_reviews:
            return f"No written reviews available for SKU '{product_sku}'."

        payload = {
            "top_positive_reviews": [{"rating": r.rating, "comment": r.comment} for r in top_reviews],
            "bottom_negative_reviews": [{"rating": r.rating, "comment": r.comment} for r in bottom_reviews]
        }
        return json.dumps(payload, indent=2)
    finally: db.close()


@tool
def product_search_warranty(product_sku: str) -> str:
    """Fetches full warranty policy details for a specific product SKU."""
    db = next(get_store_db())
    try:
        warranty_chunks = db.scalars(
            select(DocumentSearch.chunk_text)
            .where(
                DocumentSearch.sku == product_sku,
                DocumentSearch.file_name.ilike("%warranty%")
            )
        ).all()

        if not warranty_chunks:
            return f"No specific warranty document found for SKU '{product_sku}'."

        return json.dumps({
            "sku": product_sku,
            "warranty_details": "\n\n".join(warranty_chunks)
        }, indent=2)
    finally:
        db.close()