def generate_signal(stats):
    diff = abs(stats["player_pct"] - stats["banker_pct"])

    if diff < 0.1:
        return {"entry": "NO BET", "confidence": 0}

    entry = "PLAYER" if stats["player_pct"] > stats["banker_pct"] else "BANKER"
    confidence = round(diff * 100, 2)

    return {
        "entry": entry,
        "confidence": confidence
    }
