def two_of_three(a, b, c):
  return max(a*a+b*b, a*a+c*c, b*b+c*c)

def two_of_three(a, b, c):
  ab = a*a + b*b
  bc = b*b + c*c
  ca = c*c + a*a
  return max(ab, bc, ca)
