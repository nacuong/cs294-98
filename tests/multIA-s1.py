def multIA(m, n):
    i = 0
    result = 1 # 0
    while i < n:
        result *= m # +=
        i += 1
    return result
