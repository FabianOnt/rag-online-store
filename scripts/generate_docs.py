from langchain_ollama import ChatOllama
from re import search 
from json import loads, dump, load
from tqdm import tqdm
from scipy.stats import binom



llm = ChatOllama(
    base_url="http://ollama:11434",
    model="qwen3.5:4b-mlx",
    reasoning=False,
    top_k=40,
    top_p=0.9,
    temperature=0.8,
    num_predict=2500,
    num_ctx=4000
)


with open("sample-data/products.json", "r") as file:
    products = load(file)
    file.close()


# DESC, SPECS, FAQ

documents = []

pbar = tqdm(
    total=len(products), 
    desc=f"Generating documents",
    unit="step",
    dynamic_ncols=True,
    leave=False,
    mininterval=0.1
)

for i, product in enumerate(products):

    context = "I am populating an Online Store DB. " \
            f"Create an informative description for the product '{product.get('name')}' "\
            "that sounds catchy but really explains its usage. Write no more than 3 sentences, " \
            "but try to keep it between 1 and 2. " \
            "Important!: the output must only be a plain text with the description, no more text." \
            "I provide you an example of how the output should look in a short and long format. " \
            "You may decide the extension depending on the product, but try to keep it simple:\n" \
            "INPUT: SDF Automatic Coffee Machine\n" \
            "OUTPUT (SHORT VERSION): Start your day with consistency and style. The SDF Automatic Coffee Machine " \
            "delivers rich, barista-quality cups in the palm of your hand, powered by 24/7 smart " \
            "technology for every coffee lover.\n" \
            "OUTPUT (LONG VERSION): Stop compromising between time and taste. The SDF Automatic Coffee Machine " \
            "is designed for the busy professional and the coffee connoisseur alike. Whether you are " \
            "rushing out the door or enjoying a slow morning moment, this machine turns brewing into an " \
            "effortless ritual. With zero setup required, it delivers rich, aromatic flavor directly to " \
            "your cup every time—perfectly calibrated for your specific taste profile."
                
    response = llm.invoke(context)
    desc = response.content


    context = "I am populating an Online Store DB. " \
            f"Create a specifications list for the product '{product.get('name')}' with description '{desc}'. "\
            "Such list must contain physical specs (dimensions, weight, color, etc.), power output, capacity or other " \
            "specs that may be useful depending on the case. Create no more than 8 specs. " \
            "Important!: the output must only be a plain text with each element in the list in one single line, " \
            "no more text. Avoid the usage of bullet points of any kind, just write on a new line the spec." \
            "Always include weight and dimensions (in metric system, keep inches for screen size)! and the newline symbol. " \
            "I provide you an example of how the output should look.\n" \
            "INPUT (product): SDF Automatic Coffee Machine\n" \
            "INPUT (description): OUTPUT (SHORT VERSION): Start your day with consistency and style. The SDF " \
            "Automatic Coffee Machine delivers rich, barista-quality cups in the palm of your hand, powered by " \
            "24/7 smart technology for every coffee lover.\n" \
            "OUTPUT:\n" \
            "Color: Black\n" \
            "Serving capacity: 4 cups\n" \
            "Power output: 1500W\n" \
            "Weight: 3kg\n" \
            "Dimensions: 30cm x 30cm x 35cm"

    response = llm.invoke(context)
    specs = response.content


    context = "I am populating an Online Store DB. " \
            f"Create a 5 FAQ list for the product '{product.get('name')}' with description '{desc}' "\
            f"and specifications '{specs}'. " \
            "Try to write both, general and specific questions with their corresponding answer." \
            "Important!: the output must only be a plain text with each element in the list in one single line, " \
            "no more text. Avoid the usage of bullet points of any kind, just write on a new line the spec." \
            "I provide you an example of how the output should look.\n" \
            "INPUT (product): SDF Automatic Coffee Machine\n" \
            "INPUT (description): OUTPUT (SHORT VERSION): Start your day with consistency and style. The SDF " \
            "Automatic Coffee Machine delivers rich, barista-quality cups in the palm of your hand, powered by " \
            "24/7 smart technology for every coffee lover.\n" \
            "INPUT (specs):\n" \
            "Power output: 1500W\n" \
            "Weight: 3kg\n" \
            "Serving capacity: 4 cups\n" \
            "Color: Black\n" \
            "OUTPUT:\n" \
            "Q: Is this a simple one-button device, or do I need to program it?\n" \
            "A: It is a true 'set-and-forget' experience with zero programming needed. The machine reads the button you press " \
            "and automatically adjusts to brew your specific preference in under 2 minutes.\n" \
            "Q: How much effort is required for maintenance?\n" \
            "A: Maintenance is hands-off until you want it back. With its smart auto-clean function, the machine handles hygiene " \
            "automatically after every 5th brew cycle. No daily scrubbing or manual water rinses are needed; just press the " \
            "'Clean' button if there's ever a concern about flavor residue.\n" \
            "ETC... UNTIL REACHING 5 QA PAIRS."

    response = llm.invoke(context)
    faqs = response.content


    context = "I am populating an Online Store DB. " \
            f"Create a specific waranty document for the product '{product.get('name')}' with description '{desc}' "\
            f"and specifications '{specs}'. Be as extensive as you need. " \
            f"The waranty must be of {product.get('waranty')}"


    response = llm.invoke(context)
    waranty = response.content
    

    new_doc = {
        "desc": desc,
        "specs": specs,
        "faqs": faqs,
        "waranty": waranty
    }



    documents.append(new_doc)

    pbar.set_postfix({"Created": product.get("name")})
    pbar.update(1)


with open("sample-data/documents.json", "w", encoding="utf-8") as file:
    dump(documents, file, indent=4)
    file.close()