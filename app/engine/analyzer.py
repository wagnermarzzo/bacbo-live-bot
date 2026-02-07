from app.engine.signal import generate_signal
from app.engine.stats import update_stats

history = []

def process_round(result):
    history.append(result)
    stats = update_stats(history)
    signal = generate_signal(stats)
    return {
        "last_result": result,
        "signal": signal["entry"],
        "confidence": signal["confidence"],
        "history": history[-10:]
    }
