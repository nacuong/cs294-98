def double(f):
  def ff(x):
    return f(f(x))
  return ff
