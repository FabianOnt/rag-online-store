from decimal import Decimal
from typing import List, Optional, Sequence
from sqlalchemy.orm import Session
from sqlalchemy.engine import Row
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from random import randint

from services.store_db.models import Category, Product, Review, ProductDocumentChunk


def create_category(db: Session, name: str) -> Category:
    """Register a new Category."""
    category = Category(name=name)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_product(
    db: Session,
    name: str,
    price: Decimal | float,
    category_name: str,
    units: int = 0,
    discount: Decimal | float = 0.00,
) -> Product:
    """Register a new Product using category_name instead of category_id."""
    # Lookup existing Category by name
    category = db.scalar(
        select(Category).where(Category.name == category_name)
    )
    if not category:
        raise ValueError(f"Category '{category_name}' does not exist.")
    
    sku = category_name[:3].replace(" ","X") + name[:7] + str(randint(10,99))

    product = Product(
        sku=sku,
        name=name,
        price=Decimal(str(price)),
        category_id=category.id,
        units=units,
        discount=Decimal(str(discount)),
    )
    try:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_review(
    db: Session,
    product_sku: str,
    rating: int,
    comment: Optional[str] = None,
) -> Review:
    """Register a new Product Review using product_sku instead of product_id."""
    # Lookup existing Product by SKU (SKU is unique)
    product = db.scalar(
        select(Product).where(Product.sku == product_sku)
    )
    if not product:
        raise ValueError(f"Product with SKU '{product_sku}' does not exist.")

    review = Review(
        product_id=product.id,
        rating=rating,
        comment=comment,
    )
    try:
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def create_document_chunk(
    db: Session,
    file_name: str,
    doc_type: str,
    chunk_index: int,
    chunk_text: str,
    embedding: List[float],
    product_sku: Optional[str] = None,
) -> ProductDocumentChunk:
    """Register a new Document Chunk using product_sku instead of product_id."""
    product_id = None
    if product_sku:
        # Lookup existing Product by SKU
        product = db.scalar(
            select(Product).where(Product.sku == product_sku)
        )
        if not product:
            raise ValueError(f"Product with SKU '{product_sku}' does not exist.")
        product_id = product.id

    chunk = ProductDocumentChunk(
        product_id=product_id,
        file_name=file_name,
        doc_type=doc_type,
        chunk_index=chunk_index,
        chunk_text=chunk_text,
        embedding=embedding,
    )
    try:
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def search_product(db: Session, product_name: str = "") -> Sequence[Row]:
    """
    Search for products by name returning only id, sku, and name.
    If product_name is empty, returns all products.
    """
    stmt = select(Product.id, Product.sku, Product.name)
    
    if product_name:
        stmt = stmt.where(Product.name.contains(product_name))
        
    return db.execute(stmt).all()