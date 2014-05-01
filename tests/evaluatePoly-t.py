def evaluatePoly(poly, x):
    a = len(poly)
    if a == 0:
        return 0.0
    summe = 0
    for i in range(1,a):    
        summe = summe + (poly[i]*x**(i)) 
    
    return summe  

