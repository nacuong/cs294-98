import ast, sys, copy

class SynthesisVisitor(ast.NodeVisitor):
  fixes = []
  allvars = []

  def __init__(self, either_map, num_map, var_map, locs):
    self.either_map = either_map
    self.num_map = num_map
    self.var_map = var_map
    self.locs = locs

  def getFixes(self):
    return self.fixes

  """
  A visitor for either
  """
  def visit_Either(self, node):
    if node.id in self.either_map:
      fix = node.choices[self.either_map[node.id]]
      fix.lineno = node.lineno
      fix.col_offset = node.col_offset
      fix = self.visit(fix)
      if (node.lineno, node.col_offset) in self.locs:
        self.fixes.append(fix)

      return fix
    else:
      return node

  """
  A visitor for all num
  """
  def visit_AllNum(self, node):
    if node.id in self.num_map:
      fix = ast.Num(self.num_map[node.id])
      fix.lineno = node.lineno
      fix.col_offset = node.col_offset
      if (node.lineno, node.col_offset) in self.locs:
        self.fixes.append(fix)

      return fix
    else:
      return node

  """
  A visitor for all var
  """
  def visit_AllVar(self, node):
    if node.id in self.var_map:
      fix = ast.Name(self.allvars[self.var_map[node.id]], ast.Load)
      fix.lineno = node.lineno
      fix.col_offset = node.col_offset
      if (node.lineno, node.col_offset) in self.locs:
        self.fixes.append(fix)

      return fix
    else:
      return node

  """
  A visitor for num expression
  """
  def visit_Num(self, node):
    return node

  """
  A visitor for binop expression
  """
  def visit_BinOp(self, node):
    left = None
    right = None
    op = None
    for field, value in ast.iter_fields(node):
      if field == "left":
        left = value
      elif field == "op":
        op = value
      elif field == "right":
        right = value

    node.op = self.visit(op)
    node.right = self.visit(right)
    node.left = self.visit(left)

    if (node.lineno, node.col_offset) in self.locs:
      self.fixes.append(node)

    return node

  """
  A visitor for compare expression
  """
  def visit_Compare(self, node):
    left = None
    ops = None
    comparators = None
    for field, value in ast.iter_fields(node):
      if field == "left":
        left = value
      elif field == "ops":
        ops = value[0]
      elif field == "comparators":
        comparators = value[0]

    node.ops = [self.visit(ops)]
    node.left = self.visit(left)
    node.comparators = [self.visit(comparators)]

    if (node.lineno, node.col_offset) in self.locs:
      self.fixes.append(node)

    return node

  """
  A visitor for list
  """
  def visit_List(self, node):
    new_elts = []
    for field, value in ast.iter_fields(node):
      if field == "elts":
        for v in value:
          new_elts.append(self.visit(v))

    node.elts = new_elts
    if (node.lineno, node.col_offset) in self.locs:
      self.fixes.append(node)

    return node

  def visit_Subscript(self, node):
    val = None
    inx = None
    for field, value in ast.iter_fields(node):
      if field == "value":
        val = value
      elif field == "slice":
        inx = value

    node.value = self.visit(val)
    node.slice = self.visit(inx)

    if (node.lineno, node.col_offset) in self.locs:
      self.fixes.append(node)

    return node

  """
  A visitor for if expression
  """
  def visit_If(self, node):
    for field, value in ast.iter_fields(node):
      if field == "test":
        node.test = self.visit(value)
      elif field == "body":
        node.body = [self.visit(stmt) for stmt in value]
      elif field == "orelse":
        node.orelse = [self.visit(stmt) for stmt in value]

    return node

  """
  A visitor for call expression
  """
  def visit_Call(self, node):
    for field, value in ast.iter_fields(node):
      if field == "func":
        node.func = self.visit(value)
      elif field == "args":
        node.args = [self.visit(arg) for arg in value]

    return node


  """
  A visitor for unaryop expression
  """
  def visit_UnaryOp(self, node):
    op = None
    operand = None
    for field, value in ast.iter_fields(node):
      if field == "operand":
        operand = value
      elif field == "op":
        op = value

    # process op
    node.op = self.visit(op)
    # process operand
    node.left = self.visit(left)

    return node

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    lhs = None
    rhs = None
    for field, value in ast.iter_fields(node):
      if field == "targets":
        lhs = value[0]
      elif field == "value":
        rhs = value
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s." % value)

    if isinstance(lhs, ast.Name):
      node.targets = [self.visit(lhs)]
      node.value = self.visit(rhs)
    elif isinstance(lhs, ast.Tuple):
      new_lhs = []
      new_rhs = []
      for l,r in zip(lhs.elts, rhs.elts):
        new_lhs.append(self.visit(l))
        new_rhs.append(self.visit(r))

      lhs.elts = new_lhs
      rhs.elts = new_rhs

    if (node.lineno, node.col_offset) in self.locs:
      self.fixes.append(node)

    return node


  """
  A visitor for return expression
  """
  def visit_Return(self, node):
    for field, value in ast.iter_fields(node):
      if field == "value":
        node.value = self.visit(value)

    return node


  """
  A visitor for name expression
  """
  def visit_Name(self, node):
    return node

  """
  A visitor for while statement
  """
  def visit_While(self, node):
    for field, value in ast.iter_fields(node):
      if field == "test":
        node.test = self.visit(value)
      if field == "body":
        node.body = [self.visit(stmt) for stmt in value]

    return node

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    self.allvars = []
    for name in node.define:
      self.allvars.append(name)

    for field, value in ast.iter_fields(node):
      if field == "body":
        node.body = [self.visit(stmt) for stmt in value]

    return node

  def visit_Attribute(self, node):
    return node

  """
  Generic visitor for Python program. Syntax-directed translation to racket.
  Return the racket program and the mapping from (line, col) of python to
  (line, col) of racket program.
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    for field, value in ast.iter_fields(node):
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)

    return node


