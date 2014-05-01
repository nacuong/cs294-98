def computeDeriv(poly):
    if len(poly) == 1:
        return [0]
    deriv = []
    for i in range(1, len(poly)):
        deriv = deriv + [poly[i] * i]
    return deriv

