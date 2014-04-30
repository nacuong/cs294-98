def computeDeriv(poly):
    length = len(poly)-1
    i = length
    deriv = range(1,length+1)

    if len(poly) == 1:
           deriv = [0.0]
    else:      
        while i-1 >= 0:
            new = poly[i] * i
            i -= 1
            deriv[i] = new 

    return deriv
