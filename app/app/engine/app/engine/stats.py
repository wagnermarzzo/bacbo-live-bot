def update_stats(history):
    last = history[-10:]
    player = last.count("PLAYER")
    banker = last.count("BANKER")
    total = max(len(last), 1)

    return {
        "player_pct": player / total,
        "banker_pct": banker / total
    }
