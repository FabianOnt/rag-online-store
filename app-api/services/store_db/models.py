from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    units: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), server_default="0", nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="product", cascade="all, delete-orphan"
    )
    document_chunks: Mapped[List["ProductDocumentChunk"]] = relationship(
        "ProductDocumentChunk", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("units >= 0", name="chk_products_units"),
        CheckConstraint("price >= 0", name="chk_products_price"),
        CheckConstraint(
            "discount >= 0 AND discount <= 100", name="chk_products_discount"
        ),
        Index("idx_products_category_id", "category_id"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 0 AND rating <= 5", name="chk_reviews_rating"),
        Index("idx_reviews_product_id", "product_id"),
    )


class ProductDocumentChunk(Base):
    __tablename__ = "product_document_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(384), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="document_chunks"
    )

    __table_args__ = (
        Index("idx_chunks_product_id", "product_id"),
        Index("idx_chunks_doc_type", "doc_type"),
        Index(
            "idx_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class ProductSummary(Base):
    __tablename__ = "product_summary"

    sku: Mapped[str] = mapped_column(String(12), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100))
    original_price: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    discount: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    final_price: Mapped[Decimal] = mapped_column(Numeric)
    available_units: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100))
    review_count: Mapped[int] = mapped_column(BigInteger)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(2, 1))


class DocumentSearch(Base):
    __tablename__ = "document_search"

    sku: Mapped[str] = mapped_column(String(12), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    chunk_text: Mapped[str] = mapped_column(Text, primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))


class ReviewsSearch(Base):
    __tablename__ = "reviews_search"

    sku: Mapped[str] = mapped_column(String(12))
    rating: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)