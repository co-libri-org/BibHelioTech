# fastapi_sutime.py
from fastapi import FastAPI
from sutime import SUTime
from pydantic import BaseModel

app = FastAPI()

# Charger SUTime une seule fois au démarrage du serveur
sutime = SUTime()

class TextRequest(BaseModel):
    text: str

@app.post("/parse")
def parse_text(request: TextRequest):
    """Analyse un texte avec SUTime"""
    result = sutime.parse(request.text)
    return result
