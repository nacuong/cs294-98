def square(x):
    return x * x

def product(n):
    total, k = 1, 1
    while k <= n:
        total, k = square(k) * total, k + 1
    return total
