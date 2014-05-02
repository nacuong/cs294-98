import ast, sys, json, getopt, subprocess
import json
from define_visitor import DefineVisitor
from param_visitor import ParamVisitor
from optparse import OptionParser

class JSONVisitorException(Exception):
  pass

class SourceVisitor(ast.NodeVisitor):
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
  A visitor for num expression
  """
  def visit_Num(self, node):
    for field, value in ast.iter_fields(node):
      if field == "n":
        return str(value)

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

    return self.visit(left) + " " + self.op_to_string(ops) + " " + self.visit(right)

  """
  A visitor for if expression
  """
  def visit_If(self, node):
    test = None
    string = ""
    body = []
    orelse = []

    for field, value in ast.iter_fields(node):
      if field == "test":
        test = value
      elif field == "body":
        for stmt in value:
          body.append(stmt)
      elif field == "orelse":
        for stmt in value:
          orelse.append(stmt)

    string += "if " + self.visit(test) + ":\n"
    for stmt in body:
      string += "\t" + self.visit(stmt) + "\n"
    string += "else:\n"
    for stmt in orelse:
      string += "\t" + self.visit(stmt) + "\n"

    return string

  def visit_List(self, node):
    string = "["
    for field, value in ast.iter_fields(node):
      if field == "elts":
        for v in value:
          string += " " + self.visit(v) + ","
    string += "]"

    return string

  def visit_Subscript(self, node):
    string = ""
    value = ""
    inx = ""
    for field, value in ast.iter_fields(node):
      if field == "value":
        value = self.visit(value)
      elif field == "slice":
        inx = self.visit(value)

    return value + "[" + inx + "]"

  """
  A visitor for call expression
  """
  def visit_Call(self, node):
    func = None
    string = ""
    args = []
    for field, value in ast.iter_fields(node):
      if field == "func":
        func = value
      elif field == "args":
        for arg in value:
          args.append(arg)

    string += self.visit(func) + "("
    for arg in args:
      string += self.visit(arg) + ","
    string += ")"

    return string

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

    return self.visit(left) + " " + self.op_to_string(op) + " " + self.visit(right)

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    left = None
    right = None
    for field, value in ast.iter_fields(node):
      if field == "targets":
        left = value[0]
      elif field == "value":
        right = value

    return self.visit(left) + " = " + self.visit(right)  

  """
  A visitor for return expression
  """
  def visit_Return(self, node):
    for field, value in ast.iter_fields(node):
      if field == "value":
        return "return " + self.visit(value)

  """
  A visitor for name expression
  """
  def visit_Name(self, node):
    for field, value in ast.iter_fields(node):
      if field == "id":
        return value

  """
  Generic visitor for Python program. 
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      print node
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
        print value
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)

