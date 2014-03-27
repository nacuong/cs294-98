import ast
import sys
import json

class JSONVisitorException(Exception):
  pass

class RacketVisitor(ast.NodeVisitor):
  indent = 0
  assignNo = 0
  test = True
  racket = ""

  """
  """
  def indent_print(self, s):
    if self.test:
      for i in xrange(0, self.indent):
        print '  ',
      print s

  """
  """
  def print_field_value(self, field, value):
    self.indent_print(field + ":")
    self.indent = self.indent + 1
    self.indent_print(value)
    self.indent = self.indent - 1

  """
  Convert ast operator to string
  """
  def op_to_string(self, op):
    if isinstance(op, ast.Add):
      return "+"
    elif isinstance(op, ast.Mult):
      return "*"
    elif isinstance(op, ast.Sub):
      return "-"
    elif isinstance(op, ast.Div):
      return "/"
    elif isinstance(op, ast.Mod):
      return "%"
    elif isinstance(op, ast.Pow):
      return "^"
    elif isinstance(op, ast.Eq):
      return "==" # TODO: confirm this
    elif isinstance(op, ast.NotEq):
      return "!=" # TODO: confirm this
    elif isinstance(op, ast.Lt):
      return "<"
    elif isinstance(op, ast.LtE):
      return "<="
    elif isinstance(op, ast.Gt):
      return ">"
    elif isinstance(op, ast.GtE):
      return ">="
    else:
      raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % op)

  """
  A visitor for num expression
  """
  def visit_Num(self, node):
    for field, value in ast.iter_fields(node):
      if field == "n":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1
        self.racket = self.racket + " " + str(value)

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
      else:
        self.print_field_value(field, value)

    # process op
    self.indent_print("ops:")
    self.indent = self.indent + 1
    self.indent_print(ops.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.indent = self.indent - 1
    self.indent = self.indent - 1
    self.racket = self.racket + " (" + self.op_to_string(ops)

    # process left
    self.indent_print("left:")
    self.indent = self.indent + 1
    self.indent_print(left.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.visit(left)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    # process comparators
    self.indent_print("comparators:")
    self.indent = self.indent + 1
    self.indent_print(comparators.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.visit(comparators)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self.racket = self.racket + ")"


  """
  A visitor for if expression
  """
  def visit_If(self, node):
    self.racket = self.racket + "(if"
    for field, value in ast.iter_fields(node):
      if field == "test":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "body":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in value:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "orelse":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in value:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)

    self.racket = self.racket + ")\n"

  """
  A visitor for call expression
  """
  def visit_Call(self, node):
    self.racket = self.racket + "("
    for field, value in ast.iter_fields(node):
      if field == "func":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.visit(value)
        self.indent = self.indent - 1
      elif field == "args":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for arg in value:
          self.indent_print(arg.__class__.__name__ + ":")
          self.visit(arg)
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)
    self.racket = self.racket + " )\n"

  """
  A visitor for binop expression
  """
  def visit_BinOp(self, node):
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
      else:
        self.print_field_value(field, value)

    # process op
    self.indent_print("op:")
    self.indent = self.indent + 1
    self.indent_print(op.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.indent = self.indent - 1
    self.indent = self.indent - 1
    self.racket = self.racket + " (" + self.op_to_string(op)

    # process left
    self.indent_print("left:")
    self.indent = self.indent + 1
    self.indent_print(left.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.visit(left)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    # process right
    self.indent_print("right:")
    self.indent = self.indent + 1
    self.indent_print(right.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.visit(right)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self.racket = self.racket + ")"

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    self.assignNo = self.assignNo + 1
    for field, value in ast.iter_fields(node):
      if field == "targets":
        self.indent_print(field + ":")
        self.racket = self.racket + "(let (["
        self.indent = self.indent + 1
        self.indent_print(value[0].__class__.__name__ + ":")
        self.visit(value[0])
        self.indent = self.indent - 1
      elif field == "value":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)
    self.racket = self.racket + " ])\n"

  """
  A visitor for return expression
  """
  def visit_Return(self, node):
    for field, value in ast.iter_fields(node):
      if field == "value":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1

  """
  A visitor for name expression
  """
  def visit_Name(self, node):
    name = None
    for field, value in ast.iter_fields(node):
      if field == "id":
        name = value
        self.indent = self.indent + 1
        self.indent_print(field + ":" + name)
        self.indent = self.indent - 1
        self.racket = self.racket + " " + name

  """
  A visitor for function arguments.
  """
  def visit_arguments(self, node):
    args = None
    vararg = None
    kwarg = None
    defaults = None
    for field, value in ast.iter_fields(node):
      if field == "args":
        args = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for arg in args:
          self.indent_print(arg.__class__.__name__ + ":")
          self.visit(arg)
        self.indent = self.indent - 1
      elif field == "vararg":
        vararg = value
        self.print_field_value(field, value)
      elif field == "kwarg":
        kwarg = value
        self.print_field_value(field, value)
      elif field == "defaults":
        defaults = value
        self.print_field_value(field, value)

      if vararg or kwarg or defaults:
        raise JSONVisitorException("Unexpected error: Missed case: vararg, kwarg or defaults is not empty.  Please report to the TAs.")

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    name = None
    args = None
    body = None
    decorator_list = None

    for field, value in ast.iter_fields(node):
      if field == "name":
        name = value
        self.print_field_value(field, value)
        # declare a function with name
        self.racket = self.racket + "\n(define (" + name
      elif field == "args":
        args = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.racket = self.racket + ")\n"
      elif field == "body":
        body = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in body:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "decorator_list":
        decorator_list = value
        self.print_field_value(field, value)
     
    for i in xrange(0, self.assignNo):
      self.racket = self.racket + ")"

    self.racket = self.racket + ")\n"

    if decorator_list:
      raise JSONVisitorException("Unexpected error: Missed case: decorator_list is not empty.  Please report to the TAs.")


  """
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    for field, value in ast.iter_fields(node):
      self.indent_print(field + ":")
      self.indent = self.indent + 1
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
      self.indent = self.indent - 1

    return self.racket

if __name__ == '__main__':
  print(RacketVisitor().visit(ast.parse(sys.stdin.read())))
  #print(ast.dump(ast.parse(sys.stdin.read())))

