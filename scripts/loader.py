import json
import os
import random
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
ADMIN_HEADERS = {"Admin-API-Key": Path(f"secrets/app_api_admin_key").read_text().strip()}


def seed_database():
    print("Starting Data Seeding Process...\n")

    # =========================================================================
    # 1. READ AND CREATE CATEGORIES (`categories.txt`)
    # =========================================================================
    print("--- Ingesting Categories ---")
    categories_list = []
    
    with open("sample-data/categories.txt", "r", encoding="utf-8") as f:
        for line in f:
            category_name = line.strip()
            if category_name:
                categories_list.append(category_name)

    # Dictionary to map category index back to the created category name
    category_map = {}

    for idx, cat_name in enumerate(categories_list):
        res = requests.post(
            f"{BASE_URL}/admin/categories", 
            json={"name": cat_name}, 
            headers=ADMIN_HEADERS
        )
        if res.status_code == 201:
            print(f"[{idx}] Created Category: {cat_name}")
            category_map[idx] = cat_name
        elif res.status_code == 400 and "already exists" in res.text.lower():
            print(f"[{idx}] Category already exists: {cat_name}")
            category_map[idx] = cat_name
        else:
            print(f"Failed to create category {cat_name}: {res.text}")

    # =========================================================================
    # 2. READ PRODUCTS (`products.json`) & MATCH WITH CATEGORIES
    # =========================================================================
    print("\n--- Ingesting Products ---")
    with open("sample-data/products.json", "r", encoding="utf-8") as f:
        products_data = json.load(f)

    # Store created products with their corresponding index for document mapping
    created_products = []

    for idx, prod in enumerate(products_data):
        cat_idx = prod["category_id"]
        category_name = category_map.get(cat_idx)

        if not category_name:
            print(f"Skipping product {prod['name']}: Invalid category index {cat_idx}")
            continue

        product_payload = {
            "name": prod["name"],
            "units": prod["units"],
            "price": prod["price"],
            "discount": prod["discount"],
            "category_name": category_name,
        }

        res = requests.post(
            f"{BASE_URL}/admin/products", 
            json=product_payload, 
            headers=ADMIN_HEADERS
        )
        
        if res.status_code == 201:
            product_response = res.json()
            sku = product_response["sku"]  # SKU is returned automatically by API
            print(f"[{idx}] Created Product: {prod['name']} | SKU: {sku}")
            
            created_products.append({
                "sku": sku,
                "name": prod["name"],
                "warranty_text": prod.get("waranty", "")
            })
        else:
            print(f"Failed to create product {prod['name']}: {res.text}")

    # =========================================================================
    # 3. READ DOCUMENTS (`documents.json`) & UPLOAD CHUNKS VIA API
    # =========================================================================
    print("\n--- Ingesting & Chunking Documents ---")
    with open("sample-data/documents.json", "r", encoding="utf-8") as f:
        documents_data = json.load(f)

    for idx, doc in enumerate(documents_data):
        if idx >= len(created_products):
            print(f"No matching product found for document index {idx}")
            break

        prod_info = created_products[idx]
        sku = prod_info["sku"]
        product_name = prod_info["name"]

        # A. Desc + Specs combined file
        desc_specs_text = f"Product Description: {doc.get('desc', '')}\n\nTechnical Specifications: {doc.get('specs', '')}"
        res = requests.post(
            f"{BASE_URL}/admin/upload-document",
            files={"file": (f"{sku}_desc_specs.txt", desc_specs_text.encode("utf-8"), "text/plain")},
            data={"doc_type": "description_specs", "product_sku": sku},
            headers=ADMIN_HEADERS
        )
        print(f"Uploaded Desc/Specs for {product_name}: {res.status_code}")

        # B. FAQs independent file
        faqs_text = doc.get("faqs", "")
        if faqs_text.strip():
            res = requests.post(
                f"{BASE_URL}/admin/upload-document",
                files={"file": (f"{sku}_faqs.txt", faqs_text.encode("utf-8"), "text/plain")},
                data={"doc_type": "faq", "product_sku": sku},
                headers=ADMIN_HEADERS
            )
            print(f"Uploaded FAQs for {product_name}: {res.status_code}")

        # C. Warranty independent file
        warranty_text = doc.get("waranty", "") or prod_info["warranty_text"]
        if warranty_text.strip():
            res = requests.post(
                f"{BASE_URL}/admin/upload-document",
                files={"file": (f"{sku}_warranty.txt", warranty_text.encode("utf-8"), "text/plain")},
                data={"doc_type": "warranty", "product_sku": sku},
                headers=ADMIN_HEADERS
            )
            print(f"Uploaded Warranty for {product_name}: {res.status_code}")

    # =========================================================================
    # 4. READ, SHUFFLE AND POST REVIEWS (`./sample-data/reviews/`)
    # =========================================================================
    print("\n--- Ingesting & Shuffling Reviews ---")
    reviews_dir = "sample-data/reviews"
    all_reviews = []

    # Read all JSON files in the reviews folder
    if os.path.exists(reviews_dir):
        for filename in os.listdir(reviews_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(reviews_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    file_reviews = json.load(f)
                    if isinstance(file_reviews, list):
                        all_reviews.extend(file_reviews)

        # Randomize the order of all loaded reviews
        random.shuffle(all_reviews)

        print(f"Total reviews loaded and shuffled: {len(all_reviews)}")

        for idx, review in enumerate(all_reviews):
            product_idx = review.get("product_id") + 1

            # Map product_id index to SKU retrieved during product creation
            if product_idx is not None and product_idx < len(created_products):
                sku = created_products[product_idx]["sku"]

                review_payload = {
                    "product_sku": sku,
                    "rating": review.get("rating"),
                    "comment": review.get("comment"),
                }

                res = requests.post(
                    f"{BASE_URL}/customer/reviews",
                    json=review_payload
                )

                if res.status_code == 201:
                    print(f"[{idx+1}/{len(all_reviews)}] Review posted for SKU {sku}")
                else:
                    print(f"[{idx+1}/{len(all_reviews)}] Failed to post review for SKU {sku}: {res.text}")
            else:
                print(f"Skipping review: Invalid product_id index {product_idx}")
    else:
        print(f"Directory {reviews_dir} does not exist. Skipping reviews.")

    print("\n🎉 Data Seeding Complete!")


if __name__ == "__main__":
    seed_database()