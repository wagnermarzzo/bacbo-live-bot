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

sessions = {}

def new_session():
    return {
        "results_history": [],
        "signals_history": [],
        "current_signal": None,
        "cooldown_counter": 0,
        "last_dominant": None,
        "break_detected": False,
        "confirm_count": 0
    }

MAX_HISTORY = 80
WINDOW = 12
COOLDOWN_ROUNDS = 4

# =========================
# LOGIN
# =========================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <html><body style="background:#020617;color:white;text-align:center">
    <h2>Bacboo IA Final</h2>
    <form method="post">
        <input name="license" placeholder="LICENÇA" style="padding:10px;font-size:18px">
        <br><br>
        <button style="padding:10px 30px">ENTRAR</button>
    </form>
    </body></html>
    """

@app.post("/login")
def login(license: str = Form(...)):
    if license not in VALID_LICENSES:
        return HTMLResponse("<h3 style='color:red'>LICENÇA INVÁLIDA</h3>", status_code=403)

    session_id = str(uuid.uuid4())
    sessions[session_id] = new_session()

    res = RedirectResponse("/", status_code=302)
    res.set_cookie("session_id", session_id)
    return res

# =========================
# SEGURANÇA
# =========================
def get_state(request: Request):
    sid = request.cookies.get("session_id")
    if not sid or sid not in sessions:
        return None
    return sessions[sid]

# =========================
# ANALISE (mesma lógica)
# =========================
def detect_regime(recent):
    p = recent.count("PLAYER")
    b = recent.count("BANKER")
    if p >= 0.7 * len(recent): return "DOMINIO", "PLAYER"
    if b >= 0.7 * len(recent): return "DOMINIO", "BANKER"
    return "NEUTRO", None

def analyze(state):
    rh = state["results_history"]
    if len(rh) < WINDOW: return None, 0

    recent = [x for x in rh[-WINDOW:] if x != "TIE"]
    if len(recent) < 6: return None, 0

    regime, dominant = detect_regime(recent)

    if regime == "DOMINIO":
        state["last_dominant"] = dominant
        state["confirm_count"] = 0
        return None, 0

    if state["last_dominant"]:
        if recent[-1] == state["last_dominant"]:
            state["confirm_count"] += 1
        else:
            state["confirm_count"] = 0

        if state["confirm_count"] >= 2:
            state["last_dominant"] = None
            state["confirm_count"] = 0
            return recent[-1], 85

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

    if state["current_signal"]:
        state["signals_history"].append(state["current_signal"])
        state["current_signal"] = None

    state["results_history"].append(result)
    if len(state["results_history"]) > MAX_HISTORY:
        state["results_history"].pop(0)

    signal, confidence = analyze(state)
    if signal:
        state["current_signal"] = {
            "signal": signal,
            "confidence": confidence,
            "outcome": "WAIT"
        }

    return {
        "last_result": result,
        "current_signal": state["current_signal"],
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
    <html><body style="background:#020617;color:white;text-align:center">
    <h2>Bacboo IA Final</h2>
    <button onclick="send('PLAYER')">PLAYER</button>
    <button onclick="send('BANKER')">BANKER</button>
    <button onclick="send('TIE')">EMPATE</button>
    <pre id="out"></pre>
    <script>
    async function send(r){
        let res = await fetch('/round?result='+r,{method:'POST'})
        document.getElementById('out').innerText = JSON.stringify(await res.json(),null,2)
    }
    </script>
    </body></html>
    """
