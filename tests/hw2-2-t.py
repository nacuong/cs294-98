def accumulate(combiner, start, n, term):
  total, k = start, 1
  while k <= n:
    total, k = combiner(term(k), total), k + 2
  return total

def summation_using_accumulate(n, term):
  return accumulate(add, 0, n, term)

def product_using_accumulate(n, term):
  return accumulate(mul, 1, n, term)
