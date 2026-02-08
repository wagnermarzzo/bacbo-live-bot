from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BacBo Live Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ESTADO
# =========================
results_history = []
signals_history = []
current_signal = None
MAX_HISTORY = 60


# =========================
# ANÁLISE
# =========================
def analyze():
    if len(results_history) < 6:
        return None, 0

    p = results_history.count("PLAYER")
    b = results_history.count("BANKER")

    last = results_history[-1]
    streak = 1
    for i in range(len(results_history) - 2, -1, -1):
        if results_history[i] == last:
            streak += 1
        else:
            break

    if streak >= 3:
        return last, 85

    if p > b + 2:
        return "PLAYER", 75

    if b > p + 2:
        return "BANKER", 75

    return None, 0


# =========================
# API
# =========================
@app.post("/round")
def new_round(result: str):
    global current_signal

    result = result.upper()
    if result not in ["PLAYER", "BANKER", "TIE"]:
        return {"error": "INVALID"}

    # Fecha sinal anterior
    if current_signal:
        outcome = "GREEN" if result == current_signal["signal"] else "RED"
        current_signal["outcome"] = outcome
        signals_history.append(current_signal)

    # Registra resultado real
    results_history.append(result)
    if len(results_history) > MAX_HISTORY:
        results_history.pop(0)

    # Gera novo sinal
    signal, confidence = analyze()
    if signal:
        current_signal = {
            "signal": signal,
            "confidence": confidence,
            "outcome": "WAIT"
        }
    else:
        current_signal = None

    return {
        "last_result": result,
        "current_signal": current_signal,
        "signals_history": signals_history,
        "results_history": results_history
    }


# =========================
# PAINEL
# =========================
@app.get("/", response_class=HTMLResponse)
def panel():
    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BacBo Live</title>
<style>
body { background:#020617; color:white; font-family:Arial; text-align:center; }
button {
    width:90%; padding:26px; margin:10px;
    font-size:28px; border-radius:14px; border:none;
}
.player { background:#2563eb; }
.banker { background:#dc2626; }
.tie { background:#16a34a; }

.dot { width:16px; height:16px; border-radius:50%; display:inline-block; margin:2px; }
.P { background:#2563eb; }
.B { background:#dc2626; }
.T { background:#16a34a; }

.green { color:#22c55e; }
.red { color:#ef4444; }
</style>
</head>
<body>

<h2>BacBo Live Analyzer</h2>

<button class="player" onclick="send('PLAYER')">PLAYER</button>
<button class="banker" onclick="send('BANKER')">BANKER</button>
<button class="tie" onclick="send('TIE')">EMPATE</button>

<h3>Resultado Atual</h3>
<div id="result"></div>

<h3>Sinal Ativo</h3>
<div id="signal"></div>

<h3>Histórico Resultados</h3>
<div id="results"></div>

<h3>Histórico Sinais</h3>
<div id="signals"></div>

<script>
async function send(r){
    const res = await fetch('/round?result='+r, {method:'POST'})
    const d = await res.json()

    document.getElementById("result").innerText = d.last_result

    if(d.current_signal){
        document.getElementById("signal").innerText =
        d.current_signal.signal + " (" + d.current_signal.confidence + "%)"
    } else {
        document.getElementById("signal").innerText = "AGUARDANDO"
    }

    let hr = ""
    d.results_history.forEach(x=>{
        if(x==="PLAYER") hr+='<span class="dot P"></span>'
        if(x==="BANKER") hr+='<span class="dot B"></span>'
        if(x==="TIE") hr+='<span class="dot T"></span>'
    })
    document.getElementById("results").innerHTML = hr

    let hs = ""
    d.signals_history.forEach(s=>{
        hs += s.signal + " - "
        hs += s.outcome=="GREEN" ? "<span class='green'>GREEN</span>" :
              "<span class='red'>RED</span>"
        hs += "<br>"
    })
    document.getElementById("signals").innerHTML = hs
}
</script>

</body>
</html>
"""
