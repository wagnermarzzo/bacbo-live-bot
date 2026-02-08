from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Bacboo IA Pro")

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
        "confirm_count": 0,
        "mode": "CONSERVADOR",
        "confirm_required": 3,
        "base_confidence": 75,
        "cooldown": 0
    }

# =========================
# CONFIG
# =========================
MAX_HISTORY = 80
WINDOW = 12
ZIGZAG_FILTER_LEN = 4  # Evita sinais em zigue-zague

# =========================
# LOGIN
# =========================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
<!DOCTYPE html>
<html>
<body style="background:#020617;color:white;text-align:center;font-family:Arial">
<h2>Bacboo IA Pro</h2>
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

    recent = [x for x in rh[-WINDOW:] if x in ("PLAYER","BANKER")]
    if len(recent) < 6:
        return None, 0

    # Filtro zigue-zague
    if len(recent) >= ZIGZAG_FILTER_LEN:
        last_four = recent[-ZIGZAG_FILTER_LEN:]
        if len(set(last_four)) == 2 and last_four.count(last_four[0]) == 2:
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

        if state["confirm_count"] >= state.get("confirm_required",3):
            # Evita sinal durante cooldown pós RED
            if state.get("cooldown",0) > 0:
                state["cooldown"] -= 1
                return None, 0
            signal = recent[-1]
            # Confiança dinâmica: +2% por repetição do dominante
            confidence = state.get("base_confidence",75) + min(10, recent.count(state["last_dominant"])*2)
            state["last_dominant"] = None
            state["confirm_count"] = 0
            return signal, confidence

    return None, 0

# =========================
# API
# =========================
@app.post("/round")
def new_round(result: str, request: Request, mode: str = "CONSERVADOR"):
    state = get_state(request)
    if not state:
        return {"error": "LOGIN_REQUIRED"}

    result = result.upper()
    if result not in ["PLAYER","BANKER","TIE"]:
        return {"error": "INVALID"}

    # Ajusta modo
    mode = mode.upper()
    state["mode"] = mode
    if mode == "AGRESSIVO":
        state["confirm_required"] = 2
        state["base_confidence"] = 65
    else:
        state["confirm_required"] = 3
        state["base_confidence"] = 75

    # Fecha sinal anterior
    if state["current_signal"]:
        if result == "TIE":
            outcome = "PUSH"  # Meio red
        else:
            outcome = "GREEN" if result == state["current_signal"]["signal"] else "RED"
        # Se RED, ativa cooldown
        if outcome == "RED":
            state["cooldown"] = 1
        state["current_signal"]["outcome"] = outcome
        state["signals_history"].append(state["current_signal"])
        state["current_signal"] = None

    # Registra resultado
    state["results_history"].append(result)
    if len(state["results_history"]) > MAX_HISTORY:
        state["results_history"].pop(0)

    # Analisa
    signal, confidence = analyze(state)
    if signal:
        state["current_signal"] = {
            "signal": signal,
            "confidence": confidence,
            "outcome": "WAIT"
        }

    return response(state, result)

def response(state, result):
    # Hit rate sem PUSH
    valid = [s for s in state["signals_history"] if s["outcome"] in ("GREEN","RED")]
    wins = len([s for s in valid if s["outcome"]=="GREEN"])
    hit_rate = round((wins/len(valid))*100,1) if valid else 0

    return {
        "last_result": result,
        "current_signal": state["current_signal"],
        "hit_rate": hit_rate,
        "signals_history": state["signals_history"],
        "results_history": state["results_history"],
        "mode": state["mode"]
    }

# =========================
# PAINEL VISUAL
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
<title>Bacboo IA Pro - Visual</title>
<style>
body { background:#020617; color:white; font-family:Arial; text-align:center; }
button { width:90%; padding:16px; margin:6px; font-size:20px; border-radius:12px; border:none; cursor:pointer; }
.player { background:#2563eb; color:white; }
.banker { background:#dc2626; color:white; }
.tie { background:#16a34a; color:white; }
.dot { width:18px; height:18px; border-radius:50%; display:inline-block; margin:2px; }
.P { background:#2563eb; }
.B { background:#dc2626; }
.T { background:#16a34a; }
.green { color:#22c55e; font-weight:bold; }
.red { color:#ef4444; font-weight:bold; }
.push { color:#facc15; font-weight:bold; }
.signal-box { padding:12px; border-radius:12px; margin:8px auto; width:200px; font-size:22px; font-weight:bold; }
.signal-high { background:#22c55e; color:#020617; }
.signal-mid { background:#facc15; color:#020617; }
.signal-low { background:#ef4444; color:white; }
.streak { display:flex; flex-wrap:wrap; justify-content:center; margin:8px 0; }
.streak .dot { width:22px; height:22px; margin:2px; }
</style>
</head>
<body>

<h2>Bacboo IA Pro - Visual</h2>

<h3>Modo de Operação</h3>
<button onclick="setMode('CONSERVADOR')">Conservador</button>
<button onclick="setMode('AGRESSIVO')">Agressivo</button>
<p id="mode_display">Modo atual: CONSERVADOR</p>

<h3>Registrar Resultado</h3>
<button class="player" onclick="send('PLAYER')">PLAYER</button>
<button class="banker" onclick="send('BANKER')">BANKER</button>
<button class="tie" onclick="send('TIE')">EMPATE</button>

<h3>Resultado Atual</h3>
<div id="result"></div>

<h3>Sinal Atual</h3>
<div id="signal" class="signal-box">SEM SINAL</div>

<h3>Taxa de Acerto</h3>
<div id="hit"></div>

<h3>Sequência de Resultados</h3>
<div id="results" class="streak"></div>

<h3>Histórico de Sinais</h3>
<div id="signals" class="streak"></div>

<script>
let mode = "CONSERVADOR";

function setMode(m){
    mode = m;
    document.getElementById("mode_display").innerText = "Modo atual: " + mode;
}

function signalColor(conf){
    if(conf > 75) return 'signal-high';
    if(conf >= 66) return 'signal-mid';
    return 'signal-low';
}

async function send(r){
 const res = await fetch('/round?result='+r+'&mode='+mode,{method:'POST'})
 const d = await res.json()

 document.getElementById("result").innerText = d.last_result

 if(d.current_signal){
     let color_class = signalColor(d.current_signal.confidence);
     document.getElementById("signal").innerText = d.current_signal.signal + " (" + d.current_signal.confidence + "%)";
     document.getElementById("signal").className = "signal-box " + color_class;
 } else {
     document.getElementById("signal").innerText = "SEM SINAL";
     document.getElementById("signal").className = "signal-box";
 }

 document.getElementById("hit").innerText = d.hit_rate+"%"

 // Sequência de resultados
 let hr=""
 d.results_history.forEach(x=>{
  if(x=="PLAYER") hr+='<span class="dot P"></span>'
  if(x=="BANKER") hr+='<span class="dot B"></span>'
  if(x=="TIE") hr+='<span class="dot T"></span>'
 })
 document.getElementById("results").innerHTML=hr

 // Histórico de sinais
 let hs=""
 d.signals_history.forEach(s=>{
  let c = s.outcome=="GREEN" ? "green" : s.outcome=="PUSH" ? "push" : "red";
  hs+='<span class="dot '+c+'" title="'+s.signal+'"></span>'
 })
 document.getElementById("signals").innerHTML=hs
}
</script>

</body>
</html>
"""
