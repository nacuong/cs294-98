def everyOther(l):
    t=[]
    for x in range(l):
        if x%2==0:
            t.append(l[x])
    return t
