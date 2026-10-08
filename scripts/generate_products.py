from langchain_ollama import ChatOllama
from re import search 
from json import loads, dump
from tqdm import tqdm
from scipy.stats import binom

llm = ChatOllama(
    base_url="http://ollama:11434",
    model="qwen3.5:4b-mlx",
    reasoning=False,
    top_k=40,
    top_p=0.9,
    temperature=0.8,
    num_predict=2000,
    num_ctx=4000
)



with open("sample-data/categories.txt", "r") as file:
    categories = file.readlines()
    file.close()


num_products = binom.rvs(n=100,p=0.2,size=len(categories))

products = []

pbar = tqdm(
    total=sum(num_products), 
    desc=f"Generating products",
    unit="step",
    dynamic_ncols=True,
    leave=False,
    mininterval=0.1
)

for i, category in enumerate(categories):
    product_names = []
    for j in range(num_products[i]):
        while True:
            try:

                context = "I am populating an Online Store DB. " \
                        f"Create a sample product for the category {category} "\
                        "by filling the following contents in a JSON format. " \
                        "Important!: the output must only be a single JSON entry as plain text, no more text." \
                        "as I will read the text ouput with json.loads() in Python" \
                        "I provide you an example of how the output should look and the data I need.\n" \
                        "(e.g.:" \
                        "{" \
                        "   'name': 'RDS Coffee Machine'," \
                        "   'units': 230," \
                        "   'price': 213.0," \
                        "   'discount': 25.0," \
                        "   'category_id': 1" \
                        "}" \
                        ")\n" \
                        f"In this case, set category_id={i}" \
                        "You have already generated the following examples, do not repeat them: " \
                        f"{",".join(product_names if len(product_names) > 0 else [""])}"
                            
                response = llm.invoke(context)
                new_product = loads(response.content)
        
                for key in new_product.keys():
                    if key in ["name", "units", "price", "discount", "category_id"]:
                        continue
                    else:
                        raise Exception()

                break
        
            except:
                continue

        product_names.append(new_product.get("name"))
        products.append(new_product)

        pbar.set_postfix({"Created": new_product.get("name")})
        pbar.update(1)

with open("sample-data/products.json", "w", encoding="utf-8") as file:
    dump(products, file, indent=4)
    file.close()