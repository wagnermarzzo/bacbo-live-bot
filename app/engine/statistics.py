from collections import Counter

def frequencies(history, window=20):
    data = history[-window:]
    total = len(data)
    if total == 0:
        return {}

    count = Counter(data)
    return {
        k: round((v / total) * 100, 2)
        for k, v in count.items()
  }
