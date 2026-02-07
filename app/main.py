from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI(title="BacBo Live Analyzer")

# ===============================
# MEMÓRIA EM TEMPO REAL
# ===============================
history = []
greens = 0
reds = 0

# ===============================
# LÓGICA SIMPLES (BASE)
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

    # valida green/red automático
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
# PAINEL WEB
# ===============================
app.mount("/", StaticFiles(directory="static", html=True), name="static")
