import ast, copy
from synthesis_ast import Either, AllNum, AllVar, AllNumVar

class Mixer(ast.NodeVisitor):
  def __init__(self, mutators):
    self.mutators = mutators

  def generic_visit(self, node):
    nodes = []
    for mutator in self.mutators:
      mutated_node = mutator.visit(node)
      if mutated_node not in nodes:
        nodes.append(mutated_node)

    if len(nodes) > 1:
      return Either(nodes)
    else:
      return nodes[0]

class Generic01(ast.NodeVisitor):
  def generic_visit(self, node):
    return Either([AllNum(), AllVar()])

class Generic02(ast.NodeVisitor):
  def generic_visit(self, node):
    add = ast.BinOp(Either([AllNum(), AllVar()]), ast.Add(), Either([AllNum(), AllVar()]), lineno = 0, col_offset = 0)
    sub = ast.BinOp(Either([AllNum(), AllVar()]), ast.Sub(), Either([AllNum(), AllVar()]), lineno = 0, col_offset = 0)
    mult = ast.BinOp(Either([AllNum(), AllVar()]), ast.Mult(), Either([AllNum(), AllVar()]), lineno = 0, col_offset = 0)
    div = ast.BinOp(Either([AllNum(), AllVar()]), ast.Div(), Either([AllNum(), AllVar()]), lineno = 0, col_offset = 0)

    return Either([add,sub,mult,div])


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

    # visit left and right once, and reuse them?
    add = ast.BinOp(self.visit(left), ast.Add(), self.visit(right), lineno = 0, col_offset = 0)
    sub = ast.BinOp(self.visit(left), ast.Sub(), self.visit(right), lineno = 0, col_offset = 0)
    mult = ast.BinOp(self.visit(left), ast.Mult(), self.visit(right), lineno = 0, col_offset = 0)
    div = ast.BinOp(self.visit(left), ast.Div(), self.visit(right), lineno = 0, col_offset = 0)

    return Either([add,sub,mult,div])

  def visit_Compare(self, node):
    left = None
    op = None
    comparators = None
    for field, value in ast.iter_fields(node):
      if field == "left":
        left = value
      elif field == "ops":
        op = value[0]
      elif field == "comparators":
        comparators = value[0]

    left = self.visit(left)
    comparators = [self.visit(comparators)]
    # cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn
    if isinstance(op, ast.Eq) or isinstance(op, ast.NotEq) or isinstance(op, ast.Lt) or isinstance(op, ast.LtE) or isinstance(op, ast.Gt) or isinstance(op, ast.GtE):
      eq = ast.Compare(left, [ast.Eq()], comparators)
      noteq = ast.Compare(left, [ast.NotEq()], comparators)
      lt = ast.Compare(left, [ast.Lt()], comparators)
      lte = ast.Compare(left, [ast.LtE()], comparators)
      gt = ast.Compare(left, [ast.Gt()], comparators)
      gte = ast.Compare(left, [ast.GtE()], comparators)
      return Either([eq,noteq,lt,lte,gt,gte])
    elif isinstance(op, ast.Is) or isinstance(op, ast.IsNot):
      Is = ast.Compare(left, [ast.Is()], comparators)
      IsNot = ast.Compare(left, [ast.IsNot()], comparators)
      return Either([Is,IsNot])
    elif isinstance(op, ast.In) or isinstance(op, ast.NotIn):
      In = ast.Compare(left, [ast.In()], comparators)
      NotInn = ast.Compare(left, [ast.NotIn()], comparators)
      return Either([In,NotIn])

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
