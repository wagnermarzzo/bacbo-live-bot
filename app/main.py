from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BacBo IA Final")

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

MAX_HISTORY = 80
WINDOW = 12

COOLDOWN_ROUNDS = 4
cooldown_counter = 0

last_dominant = None
break_detected = False
confirm_count = 0


# =========================
# ANÁLISE
# =========================
def detect_regime(recent):
    p = recent.count("PLAYER")
    b = recent.count("BANKER")

    if p >= 0.7 * len(recent):
        return "DOMINIO", "PLAYER"
    if b >= 0.7 * len(recent):
        return "DOMINIO", "BANKER"

    # alternância
    alt = 0
    for i in range(len(recent) - 1):
        if recent[i] != recent[i + 1]:
            alt += 1
    if alt >= len(recent) - 2:
        return "ALTERNADO", None

    return "NEUTRO", None


def analyze():
    global last_dominant, break_detected, confirm_count

    if len(results_history) < WINDOW:
        return None, 0

    recent = results_history[-WINDOW:]
    ties = recent.count("TIE")
    recent = [x for x in recent if x != "TIE"]

    if len(recent) < 6:
        return None, 0

    regime, dominant = detect_regime(recent)

    # =====================
    # DOMÍNIO
    # =====================
    if regime == "DOMINIO":
        last_dominant = dominant
        break_detected = False
        confirm_count = 0
        return None, 0

    # =====================
    # CORREÇÃO
    # =====================
    if last_dominant:
        last = recent[-1]
        prev = recent[-2]

        # Quebra detectada
        if prev == last_dominant and last != last_dominant:
            break_detected = True
            confirm_count = 0
            return None, 0

        # Confirmações
        if break_detected and last == last_dominant:
            confirm_count += 1
        else:
            confirm_count = 0

        # Entrada final
        if confirm_count >= 2:
            confidence = 85
            confidence -= ties * 4
            confidence = max(confidence, 78)

            last_dominant = None
            break_detected = False
            confirm_count = 0

            return last, confidence

    return None, 0


# =========================
# API
# =========================
@app.post("/round")
def new_round(result: str):
    global current_signal, cooldown_counter

    result = result.upper()
    if result not in ["PLAYER", "BANKER", "TIE"]:
        return {"error": "INVALID"}

    # Fecha sinal anterior
    if current_signal:
        outcome = "GREEN" if result == current_signal["signal"] else "RED"
        current_signal["outcome"] = outcome
        signals_history.append(current_signal)
        current_signal = None

    # Registra resultado
    results_history.append(result)
    if len(results_history) > MAX_HISTORY:
        results_history.pop(0)

    # Cooldown
    if cooldown_counter > 0:
        cooldown_counter -= 1
        return response(result)

    # Análise
    signal, confidence = analyze()
    if signal and confidence >= 78:
        current_signal = {
            "signal": signal,
            "confidence": confidence,
            "outcome": "WAIT"
        }
        cooldown_counter = COOLDOWN_ROUNDS

    return response(result)


def response(result):
    return {
        "last_result": result,
        "current_signal": current_signal,
        "cooldown": cooldown_counter,
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
<title>BacBo IA Final</title>
<style>
body { background:#020617; color:white; font-family:Arial; text-align:center; }
button { width:92%; padding:26px; margin:10px; font-size:28px; border-radius:16px; border:none; }
.player { background:#2563eb; }
.banker { background:#dc2626; }
.tie { background:#16a34a; }

.dot { width:16px; height:16px; border-radius:50%; display:inline-block; margin:2px; }
.P { background:#2563eb; }
.B { background:#dc2626; }
.T { background:#16a34a; }

.green { color:#22c55e; font-weight:bold; }
.red { color:#ef4444; font-weight:bold; }
.cool { color:#eab308; }
</style>
</head>
<body>

<h2>BacBo IA Final</h2>

<button class="player" onclick="send('PLAYER')">PLAYER</button>
<button class="banker" onclick="send('BANKER')">BANKER</button>
<button class="tie" onclick="send('TIE')">EMPATE</button>

<h3>Resultado Atual</h3><div id="result"></div>
<h3>Sinal</h3><div id="signal"></div>
<h3>Cooldown</h3><div id="cooldown"></div>
<h3>Histórico Resultados</h3><div id="results"></div>
<h3>Histórico Sinais</h3><div id="signals"></div>

<script>
async function send(r){
 const res = await fetch('/round?result='+r,{method:'POST'})
 const d = await res.json()

 document.getElementById("result").innerText=d.last_result
 document.getElementById("signal").innerText=d.current_signal?
 d.current_signal.signal+" ("+d.current_signal.confidence+"%)":"SEM SINAL"

 document.getElementById("cooldown").innerHTML=
 d.cooldown>0?"<span class='cool'>Aguardando "+d.cooldown+" rodadas</span>":"LIBERADO"

 let hr=""
 d.results_history.forEach(x=>{
  if(x=="PLAYER")hr+='<span class="dot P"></span>'
  if(x=="BANKER")hr+='<span class="dot B"></span>'
  if(x=="TIE")hr+='<span class="dot T"></span>'
 })
 document.getElementById("results").innerHTML=hr

 let hs=""
 d.signals_history.forEach(s=>{
  hs+=s.signal+" - "+(s.outcome=="GREEN"?
  "<span class='green'>GREEN</span>":"<span class='red'>RED</span>")+"<br>"
 })
 document.getElementById("signals").innerHTML=hs
}
</script>
</body>
</html>
"""
