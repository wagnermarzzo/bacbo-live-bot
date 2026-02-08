def volatility(history, window=10):
    data = history[-window:]
    if len(data) < 3:
        return 0

    changes = 0
    for i in range(1, len(data)):
        if data[i] != data[i - 1]:
            changes += 1

    return round((changes / (len(data) - 1)) * 100, 2)
