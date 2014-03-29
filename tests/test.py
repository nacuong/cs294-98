#x = [1,2,3,4,5]

def f():
  def g(a):
    b, c = 1, 2
    #x[0] = 10
    return a + b + c
  
  y = 100
  return g(y)
