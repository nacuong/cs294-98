import ast 
import json 
import sys

class JSONVisitorException(Exception):
  pass

class ParamVisitor(ast.NodeVisitor):
  def __init__(self, main):
    self.main = main

  """
  A visitor for function arguments.
  """
  def visit_arguments(self, node):
    args = []
    vararg = None
    kwarg = None
    defaults = None
    for field, value in ast.iter_fields(node):
      if field == "args":
        for arg in value:
          for field, value in ast.iter_fields(arg):
            if field == "id":
              args.append(value)
            else:
              JSONVisitorException("Unexpected error: argument's field is not id.")
      elif field == "vararg":
        vararg = value
      elif field == "kwarg":
        kwarg = value
      elif field == "defaults":
        defaults = value

      if vararg or kwarg or defaults:
        raise JSONVisitorException("Unexpected error: Missed case: vararg, kwarg or defaults is not empty.")

    return args

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    is_main = False
    for field, value in ast.iter_fields(node):
      if field == "name" and value == self.main:
        is_main = True
      if is_main and field == "args":
        return self.visit(value)

  """
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.")

    main_args = None
    for field, value in ast.iter_fields(node):
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            ret = self.visit(item)
            if ret:
              main_args = ret
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
      elif isinstance(value, ast.AST):
        ret = self.visit(value)
        if ret:
          main_args = ret

    return main_args

if __name__ == '__main__':
  print DefineVisitor("ab_t").visit(ast.parse(sys.stdin.read()))
