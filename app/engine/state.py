history = []
MAX_HISTORY = 60
last_signal = None
confidence = 0
status = "AGUARDAR"

def add_result(result):
    history.append(result)
    if len(history) > MAX_HISTORY:
        history.pop(0)
