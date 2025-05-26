from fastapi import FastAPI
from sutime import SUTime
from pydantic import BaseModel

app = FastAPI()

# Load SUTime once only, at server start
sutime = SUTime(mark_time_ranges=True, include_range=True)

class TextRequest(BaseModel):
    text: str

@app.post("/parse")
def parse_text(request: TextRequest):
    """Text analysis with SUTime"""
    result = sutime.parse(request.text)
    return result
