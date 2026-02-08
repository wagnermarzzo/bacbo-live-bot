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
# ESTADO GLOBAL
# =========================
history = []
MAX_HISTORY = 60


# =========================
# ANÁLISE
# =========================
def analyze():
    if len(history) < 6:
        return "WAIT", 0, "NO_DATA"

    last = history[-1]
    count_player = history.count("PLAYER")
    count_banker = history.count("BANKER")

    streak = 1
    for i in range(len(history) - 2, -1, -1):
        if history[i] == last:
            streak += 1
        else:
            break

    if streak >= 3:
        return last, 85, "STREAK"

    if count_player > count_banker + 2:
        return "PLAYER", 75, "BIAS"

    if count_banker > count_player + 2:
        return "BANKER", 75, "BIAS"

    return "WAIT", 0, "NEUTRAL"


# =========================
# REGISTRO
# =========================
def register(result):
    history.append(result)
    if len(history) > MAX_HISTORY:
        history.pop(0)


# =========================
# API
# =========================
@app.post("/round")
def new_round(result: str):
    result = result.upper()
    if result not in ["PLAYER", "BANKER", "TIE"]:
        return {"error": "INVALID"}

    register(result)
    signal, confidence, status = analyze()

    return {
        "history": history,
        "signal": signal,
        "confidence": confidence,
        "status": status
    }


# =========================
# PAINEL WEB
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
body {
    background:#0f172a;
    color:white;
    font-family:Arial;
    text-align:center;
}
button {
    width:90%;
    padding:25px;
    margin:10px;
    font-size:26px;
    border-radius:12px;
    border:none;
}
.player {background:#2563eb;}
.banker {background:#dc2626;}
.tie {background:#16a34a;}

#signal {
    font-size:32px;
    margin-top:20px;
}

.dot {
    display:inline-block;
    width:18px;
    height:18px;
    border-radius:50%;
    margin:3px;
}
.P {background:#2563eb;}
.B {background:#dc2626;}
.T {background:#16a34a;}
</style>
</head>
<body>

<h2>BacBo Live Analyzer</h2>

<button class="player" onclick="send('PLAYER')">PLAYER</button>
<button class="banker" onclick="send('BANKER')">BANKER</button>
<button class="tie" onclick="send('TIE')">EMPATE</button>

<div id="signal"></div>
<div id="history"></div>

<script>
async function send(result){
    const r = await fetch('/round?result=' + result, {method:'POST'})
    const data = await r.json()

    if(data.signal !== "WAIT"){
        document.getElementById("signal").innerHTML =
        "SINAL: " + data.signal + "<br>CONF: " + data.confidence + "%"
    } else {
        document.getElementById("signal").innerHTML = "AGUARDANDO PADRÃO"
    }

    let h = ""
    data.history.forEach(r=>{
        if(r==="PLAYER") h+='<span class="dot P"></span>'
        if(r==="BANKER") h+='<span class="dot B"></span>'
        if(r==="TIE") h+='<span class="dot T"></span>'
    })
    document.getElementById("history").innerHTML = h
}
</script>

</body>
</html>
"""
