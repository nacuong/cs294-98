import ast, copy
from synthesis_ast import Either, AllNum, AllVar, AllNumVar

class PreserveStructure(ast.NodeVisitor):
  def visit_UnaryOp(self, node):
    op = None
    operand = None
    for field, value in ast.iter_fields(node):
      if field == "operand":
        operand = value
      elif field == "op":
        op = value

    invert = ast.UnaryOp(ast.Invert, self.visit(operand), lineno = 0, col_offset = 0)
    nott = ast.UnaryOp(ast.Not, self.visit(operand), lineno = 0, col_offset = 0)
    uadd = ast.UnaryOp(ast.UAdd, self.visit(operand), lineno = 0, col_offset = 0)
    usub = ast.UnaryOp(ast.USub, self.visit(operand), lineno = 0, col_offset = 0)

    return Either([invert,nott,uadd,usub])

  def visit_AugAssign(self, node):
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

    add = ast.BinOp(target, ast.Add(), self.visit(val), lineno=0, col_offset=0)
    sub = ast.BinOp(target, ast.Sub(), self.visit(val), lineno = 0, col_offset = 0)
    mult = ast.BinOp(target, ast.Mult(), self.visit(val), lineno = 0, col_offset = 0)
    div = ast.BinOp(target, ast.Div(), self.visit(val), lineno = 0, col_offset = 0)
    either = Either([add,sub,mult,div])

    return ast.Assign([target], either, lineno=node.lineno,
        col_offset=node.col_offset)

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

    add = ast.BinOp(self.visit(left), ast.Add(), self.visit(right), lineno = 0, col_offset = 0)
    sub = ast.BinOp(self.visit(left), ast.Sub(), self.visit(right), lineno = 0, col_offset = 0)
    mult = ast.BinOp(self.visit(left), ast.Mult(), self.visit(right), lineno = 0, col_offset = 0)
    div = ast.BinOp(self.visit(left), ast.Div(), self.visit(right), lineno = 0, col_offset = 0)

    return Either([add,sub,mult,div])

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

  def generic_visit(seld, node):
    return node

class PreserveStructureAndOp(ast.NodeVisitor):
  def visit_UnaryOp(self, node):
    op = None
    operand = None
    for field, value in ast.iter_fields(node):
      if field == "operand":
        operand = value
      elif field == "op":
        op = value

    return ast.UnaryOp(op, self.visit(operand), lineno=0, col_offset=0)

  def visit_AugAssign(self, node):
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

    return ast.Assign(target, op, self.visit(val), lineno=0, col_offset=0)

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
