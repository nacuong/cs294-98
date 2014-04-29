def hailstone(n):
    nn = []
    while n != 1:
        nn.append(n)
        if n % 2 == 0:
            n = n // 2      # Integer division prevents "1.0" output
        else:
            n = 3 * n + 1
    return nn
