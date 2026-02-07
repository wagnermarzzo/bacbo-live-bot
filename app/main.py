from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json, os
from app.engine.analyzer import generate_signal
from app.engine.state import state

app = FastAPI(title="BacBo Live Analyzer")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

HISTORY_FILE = "data/history.json"

def save_history(entry):
    os.makedirs("data", exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

@app.post("/round")
def new_round(result: str):
    outcome = "N/A"

    if state["last_signal"]:
        outcome = "GREEN" if result == state["last_signal"] else "RED"
        if outcome == "GREEN":
            state["greens"] += 1
        else:
            state["reds"] += 1

    signal, confidence = generate_signal()

    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "result": result,
        "signal": state["last_signal"],
        "confidence": state["last_confidence"],
        "outcome": outcome
    }

    save_history(entry)

    state["last_signal"] = signal
    state["last_confidence"] = confidence

    return {
        "signal": signal,
        "confidence": confidence,
        "greens": state["greens"],
        "reds": state["reds"]
          }
