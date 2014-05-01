def everyOther(l):
    n = len(l)
    nl = []
    for i in range(n+1):
      if i%2==1:
        nl.append(l[i])
    return nl
