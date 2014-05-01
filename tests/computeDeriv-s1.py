def computeDeriv(poly):
    length = len(poly)-1
    i = length
    deriv = range(1,length)

    if len(poly) == 1:
           deriv = [0.0]
    else:      
        while i >= 0:
            new = poly[i] * i
            i -= 1
            deriv[i] = new 

    return deriv
