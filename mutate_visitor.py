import ast, sys, copy
from mutator import OffByOne, TrySameType
from print_visitor import PrintVisitor

class JSONVisitorException(Exception):
  pass

class MutateVisitor(ast.NodeVisitor):

  def __init__(self, mutator_map):
    self.mutator_map = mutator_map
    # print self.mutator_map

  def mutate_node(self, node):
    mutated_node = self.mutator_map[(node.lineno, node.col_offset)].visit(node)
    mutated_node.lineno = node.lineno
    mutated_node.col_offset = node.col_offset
    return mutated_node
    

  """
  A visitor for num expression
  """
  def visit_Num(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
      return node

  def visit_Subscript(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
      for field, value in ast.iter_fields(node):
        if field == "value":
          node.value = self.visit(value)
        elif field == "slice":
          node.slice = self.visit(value)
      print "mutate Subsript.slice", node.slice, node.slice.__dict__
      return node

  def visit_Index(self, node):
    node.value = self.visit(node.value)
    return node

  def visit_AugAssign(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
      target = None
      op = None
      val = None
      for field, value in ast.iter_fields(node):
        if field == "target":
          target = value
        elif field == "op":
          op = value
        elif field == "value":
          val = value

      print target
      print op
      print val

      node.target = self.visit(target)
      node.val = self.visit(val)
      node.op = op

      return node

  """
  A visitor for binop expression
  """
  def visit_BinOp(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
      left = None
      op = None
      right = None
      for field, value in ast.iter_fields(node):
        if field == "left":
          left = value
        elif field == "op":
          op = value
        elif field == "right":
          right = value
          
      node.left = self.visit(left)
      node.right = self.visit(right)
      node.op = op
      return node

  def visit_BoolOp(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
      op = None
      values = None
      for field, value in ast.iter_fields(node):
        if field == "op":
          op = value
        elif field == "values":
          values = value
          
      node.op = self.visit(op)
      node.values = [self.visit(v) for v in values]
      return node

  """
  A visitor for unaryop expression
  """
  def visit_UnaryOp(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
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
  A visitor for compare expression
  """
  def visit_Compare(self, node):
    if (node.lineno, node.col_offset) in self.mutator_map:
      return self.mutate_node(node)
    else:
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
    if (node.lineno, node.col_offset) in self.mutator_map:
      mutated_node = self.mutate_node(node)

      return mutated_node
    else:
      for field, value in ast.iter_fields(node):
        if field == "func":
          node.func = self.visit(value)
        elif field == "args":
          node.args = [self.visit(arg) for arg in value]

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

    #print lhs, isinstance(lhs, ast.Name)
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
    if (node.lineno, node.col_offset) in self.mutator_map:
      mutated_node = self.mutator_map[(node.lineno, node.col_offset)].visit(node)
      mutated_node.lineno = node.lineno
      mutated_node.col_offset = node.col_offset
      return mutated_node
    else:
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

  def visit_For(self, node):
    for field, value in ast.iter_fields(node):
      if field == "target":
        node.target = self.visit(value)
      elif field == "iter":
        node.iter = self.visit(value)
      elif field == "body":
        mutated_body = []
        for item in value:
          mutated_body.append(self.visit(item))
        node.body = mutated_body

    return node

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    for field, value in ast.iter_fields(node):
      if field == "body":
        node.body = [self.visit(stmt) for stmt in value]

    return node

  """
  Generic visitor for Python program. Syntax-directed translation to racket.
  Return the racket program and the mapping from (line, col) of python to
  (line, col) of racket program.
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    print "GENERIC", node.__class__
    for field, value in ast.iter_fields(node):
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)

    return node

# (5, 15)

if __name__ == '__main__':
  # Run: python mutate_visitor.py < tests/hw2-1-s.py
  my_ast = ast.parse(sys.stdin.read())
  PrintVisitor().visit(my_ast)
  # print "-------------------------------------"
  new_ast = copy.deepcopy(my_ast)
  offbyone = OffByOne()
  sametype = TrySameType()
  # MutateVisitor({(5,15):offbyone,(5,18):sametype}).visit(new_ast)
  MutateVisitor({(7,38):sametype}).visit(new_ast)
  PrintVisitor().visit(new_ast)
