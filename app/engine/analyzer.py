import random

def generate_signal():
    signal = random.choice(["PLAYER", "BANKER"])
    confidence = random.randint(60, 85)
    return signal, confidence
