import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="BacBo Live Analyzer")

# ===============================
# MEMÓRIA
# ===============================
history = []
greens = 0
reds = 0

# ===============================
# LÓGICA DO SINAL
# ===============================
def generate_signal(last):
    if history.count(last) >= 2:
        return last
    return "BANKER" if last == "PLAYER" else "PLAYER"

# ===============================
# API - NOVA RODADA
# ===============================
@app.post("/round")
def new_round(result: str = Query(...)):
    global greens, reds

    history.append(result)
    signal = generate_signal(result)

    if len(history) > 1:
        if history[-2] == result:
            greens += 1
        else:
            reds += 1

    return JSONResponse({
        "last_result": result,
        "signal": signal,
        "confidence": min(90, 50 + history.count(result) * 10),
        "history": history[-20:],
        "greens": greens,
        "reds": reds
    })

# ===============================
# STATIC (CAMINHO ABSOLUTO)
# ===============================
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
