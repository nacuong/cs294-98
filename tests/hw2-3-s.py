def double(f):
  def ff(x):
    return f(x)
  return ff
