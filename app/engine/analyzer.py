from .statistics import frequencies
from .volatility import volatility
from .filters import allow_entry

def analyze(history):
    freq = frequencies(history, 20)
    vol = volatility(history, 10)

    score = {"PLAYER": 0, "BANKER": 0}

    if freq.get("PLAYER", 0) > freq.get("BANKER", 0):
        score["PLAYER"] += 3
    else:
        score["BANKER"] += 3

    if vol < 40:
        score["PLAYER"] += 2
        score["BANKER"] += 2

    signal = max(score, key=score.get)
    confidence = min(95, 50 + score[signal] * 10)

    if not allow_entry(confidence, vol):
        return {
            "signal": "NO_ENTRY",
            "confidence": confidence,
            "volatility": vol
        }

    return {
        "signal": signal,
        "confidence": confidence,
        "volatility": vol
    }
