CREATE VIEW product_summary AS
SELECT 
    p.sku AS sku,
    p.name AS product_name,
    p.price AS original_price,
    p.discount AS discount,
    (p.price * (100 - p.discount) / 100.0) AS final_price,
    p.units AS available_units,
    c.name AS category,
    COUNT(r.id) AS review_count,
    COALESCE(AVG(r.rating), 0)::NUMERIC(2,1) AS avg_rating
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY 
    p.sku, 
    p.name, 
    p.price, 
    p.discount, 
    p.units, 
    c.name;


CREATE VIEW document_search AS
SELECT 
    p.sku AS sku, 
    d.chunk_text AS chunk_text, 
    d.file_name AS file_name, 
    d.embedding AS embedding
FROM product_document_chunks d
JOIN products p ON p.id = d.product_id;


CREATE VIEW reviews_search AS
SELECT
    p.sku AS sku,
    r.rating AS rating,
    r.comment AS comment
FROM reviews r
JOIN products p ON p.id = r.product_id;