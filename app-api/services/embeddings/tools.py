import requests
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException

def get_embedding(text_input: str) -> Tuple[List[str], List[List[float]]]:
    res = requests.post(
        f"http://embeddings-api:8000/admin/embedd", 
        json={"text": text_input}, 
        headers={"Admin-API-Key": Path(f"/run/secrets/embeddings_api_admin_key").read_text().strip()}
    )
    print(res)
    if res.status_code == 201:
        response = res.json()
        return response["chunks"], response["embeddings"]
    else:
        raise HTTPException(status_code=400, detail="Error during embedding text")