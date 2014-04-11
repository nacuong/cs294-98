def hailstone(n):
  length = 1
  while n != 1:
    if n % 2 == 0:
      n = floor(n / 2)
    else:
      n = 3*n + 1
    length = length + 1
  return length
