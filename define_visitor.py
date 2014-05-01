import ast 
import json 
import sys

class JSONVisitorException(Exception):
  pass


def lookup(table,val):
  if val in table:
    return True
  elif table["__up__"]:
    return lookup(table["__up__"],val)
  else:
    return False

primitives = {"add": "+", "sub": "-"}

class DefineVisitor(ast.NodeVisitor):
  env = {"__up__": None}

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    for field, value in ast.iter_fields(node):
      if field == "targets":
        # print "targets = ", value[0]
        lhs = value[0]
        if isinstance(lhs,ast.Name):
          self.visit_Lhs(value[0])
        elif isinstance(lhs,ast.Tuple):
          for l in lhs.elts:
            self.visit_Lhs(l)
        else:
          JSONVisitorException("Unexpected error: in visit_Assign Missed case: %s." \
                                 % lhs)
      elif field == "value":
        self.visit(value)

  """
  A visitor for lhs expression
  """
  def visit_Lhs(self, node):
    name = None
    for field, value in ast.iter_fields(node):
      if field == "id":
        if not lookup(self.env,value):
          # print "Define var: ", value          
          self.env[value] = "var"


  """
  A visitor for name expression
  """
  def visit_Name(self, node):
    name = None
    for field, value in ast.iter_fields(node):
      if field == "id":
        if not lookup(self.env,value):
          # primitive
          # print "Primitive value = ", value
          if value in primitives:
            node.racket = primitives[value]

  """
  A visitor for if expression
  """
  def visit_If(self, node):
    for field, value in ast.iter_fields(node):
      if field == "body":
        for stmt in value:
          self.visit(stmt)
      elif field == "orelse":
        for stmt in value:
          self.visit(stmt)

  # def visit_For(self, node):
  #   self.env[node.target.id] = "var"

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
        for arg in args:
          #print "Arg: ", arg
          for field, value in ast.iter_fields(arg):
            if field == "id":
              #print "Define arg: ", value
              self.env[value] = "arg"
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

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    self.env = {"__up__": self.env}

    for field, value in ast.iter_fields(node):
      if field == "body":
        body = value
        for stmt in body:
          self.visit(stmt)
      elif field == "args":
        #print "FunctionDef: args: ", value
        self.visit(value)

    node.define = self.env
    self.env = self.env["__up__"]
    del node.define["__up__"]
    #print "Def define: ", node.define

  """
  A visitor for module.
  """
  def visit_Module(self, node):
    self.env = {"__up__": self.env}

    for field, value in ast.iter_fields(node):
      #print "Module: field = ", field, ", value = ", value
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)

    node.define = self.env
    self.env = self.env["__up__"]
    del node.define["__up__"]
    #print "Module define: ", node.define

  """
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.")

    #print "node: ", node
    for field, value in ast.iter_fields(node):
      #print "field: ", field, " value: ", value
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)

  

if __name__ == '__main__':
  DefineVisitor().visit(ast.parse(sys.stdin.read()))
