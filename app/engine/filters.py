def allow_entry(confidence, volatility):
    if confidence < 65:
        return False
    if volatility > 70:
        return False
    return True
