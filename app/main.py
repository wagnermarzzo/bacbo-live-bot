from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.state import add_result, history
from app.analyzer import generate_signal
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.post("/result/{value}")
def post_result(value: str):
    value = value.upper()
    if value not in ["PLAYER", "BANKER", "TIE"]:
        return JSONResponse({"error": "Resultado inválido"}, status_code=400)

    add_result(value)
    signal, conf, status = generate_signal()

    return {
        "history": history,
        "signal": signal,
        "confidence": conf,
        "status": status
    }
