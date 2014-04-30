import ast, sys, json, getopt, subprocess
import json
from define_visitor import DefineVisitor
from param_visitor import ParamVisitor
from optparse import OptionParser

class JSONVisitorException(Exception):
  pass

class PrintVisitor(ast.NodeVisitor):
  indent = 0

  """
  Print ast with indentation
  """
  def indent_print(self, s):
    for i in xrange(0, self.indent):
      print '  ',
    print s

  """
  Print all field/value pairs with indentation
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
      raise JSONVisitorException("Unexpected error: Missed case: %s." % op)

  """
  A visitor for either
  """
  def visit_Either(self, node):
    self.indent_print(node.__class__.__name__ + ":")
    for field, value in ast.iter_fields(node):
      if field == "choices":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1
      elif field == "id":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1

  def visit_AllNum(self,node):
    self.indent_print(node.__class__.__name__ + ":")
    for field, value in ast.iter_fields(node):
      if field == "id":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1

  def visit_AllVar(self,node):
    self.indent_print(node.__class__.__name__ + ":")
    for field, value in ast.iter_fields(node):
      if field == "id":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1

  def visit_AllNumVar(self,node):
    self.indent_print(node.__class__.__name__ + ":")
    for field, value in ast.iter_fields(node):
      if field == "id":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1
        

  """
  A visitor for num expression
  """
  def visit_Num(self, node):
    for field, value in ast.iter_fields(node):
      if field == "n":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1

    if 'lineno' in node.__dict__:
      self.indent = self.indent + 1
      self.indent_print("line,col:" + str(node.lineno) + "," + str(node.col_offset))
      self.indent = self.indent - 1

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


  """
  A visitor for if expression
  """
  def visit_If(self, node):
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

  """
  A visitor for call expression
  """
  def visit_Call(self, node):
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

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    for field, value in ast.iter_fields(node):
      if field == "targets":
        self.indent_print(field + ":")
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
        raise JSONVisitorException("Unexpected error: Missed case: %s." % value)

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

  """
  A visitor for while statement
  """
  # def visit_While(self, node):
  #   for field, value in ast.iter_fields(node):
  #     if field == "test":
  #       self.indent_print(field + ":")
  #       self.indent = self.indent + 1
  #       self.indent_print(value.__class__.__name__ + ":")
  #       self.indent = self.indent + 1
  #       self.visit(value)
  #       self.indent = self.indent - 1
  #       self.indent = self.indent - 1
  #     if field == "body":
  #       self.indent_print(field + ":")
  #       self.indent = self.indent + 1
  #       for stmt in value:
  #         self.indent = self.indent + 1
  #         self.indent_print(value.__class__.__name__ + ":")
  #         self.visit(stmt)
  #         self.indent = self.indent - 1
  #       self.indent = self.indent - 1

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
      elif field == "args":
        args = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
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

    if decorator_list:
      raise JSONVisitorException("Unexpected error: Missed case: decorator_list is not empty.")

  """
  Generic visitor for Python program. Syntax-directed translation to racket.
  Return the racket program and the mapping from (line, col) of python to
  (line, col) of racket program.
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      print node
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    for field, value in ast.iter_fields(node):
      #print "field: ", field, " value: ", value
      self.indent_print(field + ":")
      self.indent = self.indent + 1
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.indent_print(item.__class__.__name__ + ":")
            self.indent = self.indent + 1
            self.visit(item)
            self.indent = self.indent - 1
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)
      self.indent = self.indent - 1

if __name__ == '__main__':
  tree = ast.parse(sys.stdin.read())
  print ast.iter_fields(tree)
  print(ast.dump(tree))
  PrintVisitor().visit(tree)
  print tree._fields

