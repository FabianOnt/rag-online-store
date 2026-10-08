CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    sku CHAR(12) NOT NULL,
    name VARCHAR(100) NOT NULL,
    units INT NOT NULL DEFAULT 0 CHECK (units >= 0),
    price NUMERIC(7,2) NOT NULL CHECK (price >= 0),
    discount NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 100), -- Percentage
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    rating INT NOT NULL DEFAULT 0 CHECK (rating >= 0 AND rating <= 5),
    comment TEXT NULL
);

CREATE TABLE product_document_chunks (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) NOT NULL, -- e.g., 'faq', 'care_guide', 'warranty', 'review'
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    -- metadata JSONB DEFAULT '{}'::jsonb, -- Flexible metadata (e.g., section title, tags)
    embedding vector(384) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE INDEX idx_products_category_id ON products(category_id);

CREATE INDEX idx_reviews_product_id ON reviews(product_id);

CREATE INDEX idx_chunks_product_id ON product_document_chunks(product_id);
CREATE INDEX idx_chunks_doc_type ON product_document_chunks(doc_type);

CREATE INDEX idx_chunks_embedding_hnsw ON product_document_chunks USING hnsw (embedding vector_cosine_ops);