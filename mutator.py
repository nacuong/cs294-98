import ast, copy
from synthesis_ast import Either, AllNum, AllVar, AllNumVar

class PreserveStructure(ast.NodeVisitor):
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

    add = ast.BinOp(self.visit(left), ast.Add(), self.visit(right), lineno = 0,
        col_offset = 0)
    sub = ast.BinOp(self.visit(left), ast.Sub(), self.visit(right), lineno = 0,
        col_offset = 0)
    mult = ast.BinOp(self.visit(left), ast.Mult(), self.visit(right), lineno = 0,
        col_offset = 0)
    div = ast.BinOp(self.visit(left), ast.Div(), self.visit(right), lineno = 0,
        col_offset = 0)

    return Either([add,sub,mult,div])

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

  def generic_visit(seld, node):
    return node

class PreserveStructureAndOp(ast.NodeVisitor):
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

    return ast.BinOp(self.visit(left), op, self.visit(right), lineno = 0,
        col_offset = 0)

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

  def generic_visit(seld, node):
    return node

class OffByOne(ast.NodeVisitor):

  def generic_visit(self, node):
    plus = ast.BinOp(copy.deepcopy(node),ast.Add(),ast.Num(1, lineno=0,
      col_offset=0), lineno=0, col_offset=0)
    minus = ast.BinOp(copy.deepcopy(node),ast.Sub(),ast.Num(1, lineno=0,
      col_offset=0), lineno=0, col_offset=0)
    return Either([plus,minus])


class TrySameType(ast.NodeVisitor):

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

  def generic_visit(self, node):
    return node
