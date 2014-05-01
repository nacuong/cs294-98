def evaluatePoly(poly, x):
    ans = 0

    degree = len(poly)

    for index in range(0,degree):
        ans += (poly[index] * (x ** index))
    return ans

