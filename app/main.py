from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Bacboo IA Final")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LICENÇAS
# =========================
VALID_LICENSES = {
    "BACBOO-IA-9F3K-1A",
    "BACBOO-IA-7Q2M-4B",
    "BACBOO-IA-X8P9-9C",
    "BACBOO-IA-LM22-7D",
    "BACBOO-IA-5ZK4-8E",
}

# =========================
# SESSÕES
# =========================
sessions = {}

def new_session():
    return {
        "results_history": [],
        "signals_history": [],
        "current_signal": None,
        "last_dominant": None,
        "confirm_count": 0
    }

# =========================
# CONFIG
# =========================
MAX_HISTORY = 80
WINDOW = 12
CONFIRM_REQUIRED = 1   # ✅ confirmação mínima
BASE_CONFIDENCE = 72   # 📉 confiança reduzida

# =========================
# LOGIN
# =========================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
<!DOCTYPE html>
<html>
<body style="background:#020617;color:white;text-align:center;font-family:Arial">
<h2>Bacboo IA Final</h2>
<form method="post">
<input name="license" placeholder="LICENÇA" style="padding:14px;font-size:18px" required>
<br><br>
<button style="padding:14px 40px;font-size:18px">ENTRAR</button>
</form>
</body>
</html>
"""

@app.post("/login")
def login(license: str = Form(...)):
    if license not in VALID_LICENSES:
        return HTMLResponse("<h3 style='color:red'>LICENÇA INVÁLIDA</h3>", status_code=403)

    sid = str(uuid.uuid4())
    sessions[sid] = new_session()

    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie("session_id", sid, httponly=True)
    return resp

# =========================
# SESSÃO
# =========================
def get_state(request: Request):
    sid = request.cookies.get("session_id")
    return sessions.get(sid)

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

    return "NEUTRO", None

def analyze(state):
    rh = state["results_history"]

    if len(rh) < WINDOW:
        return None, 0

    recent = [x for x in rh[-WINDOW:] if x in ("PLAYER", "BANKER")]
    if len(recent) < 6:
        return None, 0

    regime, dominant = detect_regime(recent)

    # 🔒 Detecta domínio
    if regime == "DOMINIO":
        state["last_dominant"] = dominant
        state["confirm_count"] = 0
        return None, 0

    # 🔓 Quebra confirmada
    if state["last_dominant"]:
        if recent[-1] != state["last_dominant"]:
            state["confirm_count"] += 1
        else:
            state["confirm_count"] = 0

        if state["confirm_count"] >= CONFIRM_REQUIRED:
            signal = recent[-1]
            state["last_dominant"] = None
            state["confirm_count"] = 0
            return signal, BASE_CONFIDENCE

    return None, 0

# =========================
# API
# =========================
@app.post("/round")
def new_round(result: str, request: Request):
    state = get_state(request)
    if not state:
        return {"error": "LOGIN_REQUIRED"}

    result = result.upper()
    if result not in ["PLAYER", "BANKER", "TIE"]:
        return {"error": "INVALID"}

    # 📌 Fecha sinal anterior
    if state["current_signal"] and result != "TIE":
        outcome = "GREEN" if result == state["current_signal"]["signal"] else "RED"
        state["current_signal"]["outcome"] = outcome
        state["signals_history"].append(state["current_signal"])
        state["current_signal"] = None

    # 📊 Registra resultado
    state["results_history"].append(result)
    if len(state["results_history"]) > MAX_HISTORY:
        state["results_history"].pop(0)

    # 🧠 Analisa
    signal, confidence = analyze(state)
    if signal:
        state["current_signal"] = {
            "signal": signal,
            "confidence": confidence,
            "outcome": "WAIT"
        }

    return response(state, result)

def response(state, result):
    total = len(state["signals_history"])
    wins = len([s for s in state["signals_history"] if s["outcome"] == "GREEN"])
    hit_rate = round((wins / total) * 100, 1) if total > 0 else 0

    return {
        "last_result": result,
        "current_signal": state["current_signal"],
        "hit_rate": hit_rate,
        "signals_history": state["signals_history"],
        "results_history": state["results_history"]
    }

# =========================
# PAINEL
# =========================
@app.get("/", response_class=HTMLResponse)
def panel(request: Request):
    if not get_state(request):
        return RedirectResponse("/login")

    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bacboo IA Final</title>
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
</style>
</head>
<body>

<h2>Bacboo IA Final</h2>

<button class="player" onclick="send('PLAYER')">PLAYER</button>
<button class="banker" onclick="send('BANKER')">BANKER</button>
<button class="tie" onclick="send('TIE')">EMPATE</button>

<h3>Resultado Atual</h3><div id="result"></div>
<h3>Sinal</h3><div id="signal"></div>
<h3>Taxa de Acerto</h3><div id="hit"></div>
<h3>Histórico Resultados</h3><div id="results"></div>
<h3>Histórico Sinais</h3><div id="signals"></div>

<script>
async function send(r){
 const res = await fetch('/round?result='+r,{method:'POST'})
 const d = await res.json()

 document.getElementById("result").innerText = d.last_result

 document.getElementById("signal").innerText =
 d.current_signal ? d.current_signal.signal+" ("+d.current_signal.confidence+"%)" : "SEM SINAL"

 document.getElementById("hit").innerText = d.hit_rate+"%"

 let hr=""
 d.results_history.forEach(x=>{
  if(x=="PLAYER")hr+='<span class="dot P"></span>'
  if(x=="BANKER")hr+='<span class="dot B"></span>'
  if(x=="TIE")hr+='<span class="dot T"></span>'
 })
 document.getElementById("results").innerHTML=hr

 let hs=""
 d.signals_history.forEach(s=>{
  hs+=s.signal+" - "+(s.outcome=="GREEN"
   ? "<span class='green'>GREEN</span>"
   : "<span class='red'>RED</span>")+"<br>"
 })
 document.getElementById("signals").innerHTML=hs
}
</script>

</body>
</html>
"""
