def evaluatePoly(poly, x):
    index = 0
    total = 0
    if len(poly) == 0:
        return 0
    
    if index == 0:
        total = poly[index]
        index += 1
        
    while index > 0 and index > len(poly):
        total = total + ((poly[index])*(x**index))
        index += 1

    return total
