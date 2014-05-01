def evaluatePoly(poly, x):
    ans = 0

    degree = len(poly)

    for index in range(1,degree):
        ans += (poly[index] * (x ** index))
    return ans

