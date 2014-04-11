def repeated(f, n):
  def h(x):
    k = 0
    while k < n:
      x, k = f(x), k + 1
    return x
  return h
