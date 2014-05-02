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

#############  Super class for all mutators. ############
class Mutator(ast.NodeVisitor):
  def visit_AugAssign(self, node):
    return ast.AugAssign(self.visit(node.target), node.op, node.value , lineno=node.lineno, col_offset=node.col_offset)

  def visit_BinOp(self, node):
    return ast.BinOp(self.visit(node.left), node.op, node.right, lineno=node.lineno, col_offset=node.col_offset)

  def visit_BoolOp(self, node):
    values = [x for x in node.values]
    values[0] = self.visit(values[0])
    return ast.BoolOp(node.op, values, lineno=node.lineno, col_offset=node.col_offset)

  def visit_Compare(self, node):
    return ast.Compare(self.visit(node.left), node.ops, node.comparators, lineno=node.lineno, col_offset=node.col_offset)
  
  def generic_visit(self, node):
    return node


class PreserveStructure(Mutator):
  def visit_UnaryOp(self, node):
    op = node.op
    operand = node.operand

    invert = ast.UnaryOp(ast.Invert, self.visit(operand), lineno = 0, col_offset = 0)
    nott = ast.UnaryOp(ast.Not, self.visit(operand), lineno = 0, col_offset = 0)
    uadd = ast.UnaryOp(ast.UAdd, self.visit(operand), lineno = 0, col_offset = 0)
    usub = ast.UnaryOp(ast.USub, self.visit(operand), lineno = 0, col_offset = 0)

    return Either([invert,nott,uadd,usub])

  def visit_AugAssign(self, node):
    target = node.target
    op = node.op
    val = node.value

    add = ast.BinOp(target, ast.Add(), self.visit(val), lineno=0, col_offset=0)
    sub = ast.BinOp(target, ast.Sub(), self.visit(val), lineno = 0, col_offset = 0)
    mult = ast.BinOp(target, ast.Mult(), self.visit(val), lineno = 0, col_offset = 0)
    div = ast.BinOp(target, ast.Div(), self.visit(val), lineno = 0, col_offset = 0)
    either = Either([add,sub,mult,div])

    return ast.Assign(target, either, lineno=node.lineno,
        col_offset=node.col_offset)

  def visit_BinOp(self, node):
    left = node.left
    op = node.op
    right = node.right

    add = ast.BinOp(self.visit(left), ast.Add(), self.visit(right), lineno = 0, col_offset = 0)
    sub = ast.BinOp(self.visit(left), ast.Sub(), self.visit(right), lineno = 0, col_offset = 0)
    mult = ast.BinOp(self.visit(left), ast.Mult(), self.visit(right), lineno = 0, col_offset = 0)
    div = ast.BinOp(self.visit(left), ast.Div(), self.visit(right), lineno = 0, col_offset = 0)

    return Either([add,sub,mult,div])

  def visit_Compare(self, node):
    left = node.left
    op = node.op[0]
    comparators = node.comparators[0]

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
    return node

  def visit_BoolOp(self, node):
    op = node.op
    values = node.values

    And = ast.BoolOp(ast.And(), values)
    Or = ast.BoolOp(ast.Or(), values)
    return Either([And,Or])

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

class PreserveStructureAndOp(Mutator):
  def visit_UnaryOp(self, node):
    return ast.UnaryOp(node.op, self.visit(node.operand), lineno=0, col_offset=0)

  def visit_AugAssign(self, node):
    return ast.Assign(node.target, node.op, self.visit(node.value), lineno=0, col_offset=0)

  def visit_BinOp(self, node):
    return ast.BinOp(self.visit(node.left), node.op, self.visit(node.right), lineno = 0,
        col_offset = 0)

  def visit_BoolOp(self, node):
    return ast.BoolOp(node.op, [self.visit(v) for v in node.values], lineno = 0, 
                      col_offset = 0)

  def visit_Compare(self, node):
    return ast.Compare(self.visit(node.left), self.ops, [self.visit(node.comparators[0])])

  def visit_Num(self, node):
      return AllNum()

  def visit_Name(self, node):
    return AllVar()

class OffByOne(Mutator):

  def modify(self, node):
    plus = ast.BinOp(copy.deepcopy(node),ast.Add(),ast.Num(1, lineno=0,
                                                           col_offset=0), lineno=0, col_offset=0)
    minus = ast.BinOp(copy.deepcopy(node),ast.Sub(),ast.Num(1, lineno=0,
                                                            col_offset=0), lineno=0, col_offset=0)
    return Either([node,plus,minus])

  def visit_Num(self, node):
    return self.modify(node)

  def visit_Name(self, node):
    return self.modify(node)

  def visit_Subscript(self, node):
    return self.modify(node)

  def visit_BinOp(self, node):
    return self.modify(node)

  def visit_UnaryOp(self, node):
    if isinstance(node.op, ast.UAdd) or isinstance(node.op, ast.USub):
      return self.modify(node)
    else:
      return node

class TrySameType(Mutator):

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()


