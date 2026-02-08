from app.state import history

def generate_signal():
    if len(history) < 10:
        return None, 0, "AGUARDAR"

    weight = 1
    scores = {"PLAYER": 0, "BANKER": 0, "TIE": 0}

    for r in reversed(history):
        scores[r] += weight
        weight += 1

    total = scores["PLAYER"] + scores["BANKER"]
    if total == 0:
        return None, 0, "AGUARDAR"

    p_player = scores["PLAYER"] / total * 100
    p_banker = scores["BANKER"] / total * 100

    if 45 <= p_player <= 55:
        return None, 0, "EQUILÍBRIO"

    if p_player > p_banker:
        return "PLAYER", round(p_player, 2), "ENTRADA"
    else:
        return "BANKER", round(p_banker, 2), "ENTRADA"
