from fastapi import FastAPI
from app.engine.analyzer import process_round

app = FastAPI(title="BacBo Live Analyzer")

@app.post("/round")
def new_round(result: str):
    return process_round(result)
