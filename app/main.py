from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.engine.analyzer import process_round

app = FastAPI(
    title="BacBo Live Analyzer",
    version="0.1.0"
)

@app.post("/round")
def new_round(result: str):
    return process_round(result)

# painel em /panel
app.mount("/panel", StaticFiles(directory="app/static", html=True), name="panel")
