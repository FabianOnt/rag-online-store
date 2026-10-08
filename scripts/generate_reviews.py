from langchain_ollama import ChatOllama
from json import load, dump
from tqdm import tqdm
from scipy.stats import binom, multinomial, dirichlet

import numpy as np
import requests


def flush_ollama_memory():
    requests.post(
        "http://ollama-lb:11434/api/generate",
        json={"model": "qwen3.5:4b-mlx", "keep_alive": 0}
    )

def normalize(x: np.ndarray, p:int=2) -> np.ndarray:
    return x / np.linalg.norm(x, ord=p)

llm = ChatOllama(
    base_url="http://ollama-lb:11434",
    model="qwen3.5:4b-mlx",
    reasoning=False,
    top_k=40,
    top_p=0.9,
    temperature=0.5,
    num_predict=500,
    num_ctx=1000
)

with open("sample-data/products.json", "r") as file:
    products = load(file)
    file.close()

with open("sample-data/documents.json", "r") as file:
    documents = load(file)
    file.close()

num_commented_reviews = binom.rvs(n=14,p=0.4,size=len(products)) + 6
num_uncommented_reviews = binom.rvs(n=250,p=0.3,size=len(products)) + 1

pbar = tqdm(
    total=sum(num_commented_reviews) + sum(num_uncommented_reviews), 
    desc=f"Generating products",
    unit="step",
    dynamic_ncols=True,
    leave=False,
    mininterval=0.1
)

BATCH_SIZE = 500

reviews = [None] * BATCH_SIZE

k = 0
batch = 0
for i, (product, doc) in enumerate(zip(products, documents)):
    probs = normalize(dirichlet(alpha=np.array([0.7,0.7,0.8,0.9,1.0])*0.6).rvs(1).reshape(-1) + 0.02,1)

    rating_uncommented = multinomial(n=1, p=probs).rvs(num_uncommented_reviews[i]).argmax(axis=1) + 1
    for j in range(num_uncommented_reviews[i]):
        new_review = {
            "product_id": i,
            "rating": int(rating_uncommented[j]),
            "comment": None
        }
        reviews[k] = new_review

        pbar.set_postfix({"Created review for": product.get("name")})
        pbar.update(1)
        k += 1

        if k == BATCH_SIZE:
            with open(f"sample-data/reviews/{batch:05d}.json", "w", encoding="utf-8") as file:
                dump(reviews, file, indent=4)
                file.close()
            reviews = [None] * BATCH_SIZE
            batch += 1
            k = 0

    rating_commented = np.zeros(num_commented_reviews[i], dtype=np.int32)
    rating_commented[:num_commented_reviews[i]-5] = multinomial(n=1, p=probs).rvs(num_commented_reviews[i]-5).argmax(axis=1) + 1
    rating_commented[num_commented_reviews[i]-5:] = [1,2,3,4,5]

    context = "I am populating the rewviews of an Online Store DB. " \
        f"Create a list of 5 good and 5 bad (distinct) characteristics of the product " \
        f"'{product.get('name')}'. It costs ${product.get('price')} and has a {product.get('discount')}% discount "\
        f"with a {product.get('waranty')} waranty. The product is described as follows: {doc.get('desc')}\n{doc.get('specs')}. " \
        "This list will be used as reference to generate sample reviews. I want the output to be plain text " \
        "with only the following structure: " \
        "PROS:\n" \
        "* pro_characterisitc_1\n" \
        "* ...\n" \
        "* pro_characterisitc_5\n" \
        "CONS:\n" \
        "* con_characterisitc_1\n" \
        "* ...\n" \
        "* con_characterisitc_5\n" \

    response = llm.invoke(context)
    pros_cons = response.content

    for j in range(num_commented_reviews[i]):
        context = "I am populating the rewviews of an Online Store DB. " \
            "You are an average american person that is sharing its review of a product in an online store. " \
            f"Create a short comment for a {rating_commented[j]}-star (1-5 star system) review about the product " \
            f"'{product.get('name')}'. It costs ${product.get('price')} and has a {product.get('discount')}% discount "\
            f"with a {product.get('waranty')} waranty. The product is described as follows: {doc.get('desc')}\n{doc.get('specs')}\n" \
            f"Consider that the product has the following pros & cons, take one or two according to the rating and write a comment: \n {pros_cons}" \
            f"{'Give a strong polarized opinion.' if np.random.rand() > 0.35 and rating_commented[j] != 3 else ''}"
                
        response = llm.invoke(context)
        new_comment = response.content

        new_review = {
            "product_id": i,
            "rating": int(rating_commented[j]),
            "comment": new_comment
        }
        reviews[k] = new_review

        #print(f"[{product.get('name')}] ({rating_commented[j]}) {new_comment}")

        pbar.set_postfix({"Created review for": product.get("name")})
        pbar.update(1)
        k += 1

        if k == BATCH_SIZE:
            with open(f"sample-data/reviews/{batch:05d}.json", "w", encoding="utf-8") as file:
                dump(reviews, file, indent=4)
                file.close()
            reviews = [None] * BATCH_SIZE
            batch += 1
            k = 0

        if j > 0 & j % 50 == 0:
            flush_ollama_memory()
    
if k > 0:
    with open(f"sample-data/reviews/{batch:05d}.json", "w", encoding="utf-8") as file:
        dump(reviews, file, indent=4)
        file.close()
    reviews = [None] * BATCH_SIZE
    batch += 1
    k = 0

    flush_ollama_memory()