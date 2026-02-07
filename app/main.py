from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.engine.analyzer import process_round

app = FastAPI(title="BacBo Live Analyzer")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.post("/round")
def new_round(result: str):
    return process_round(result)
