def a_plus_abs_b(a, b):
  if b < 0:
    op = sub
  else:
    op = add
  return op(a, b)
