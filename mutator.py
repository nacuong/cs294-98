import ast, copy
from synthesis_ast import Either, AllNum, AllVar, AllNumVar

class OffByOne(ast.NodeVisitor):

  def generic_visit(self, node):
    plus = ast.BinOp(copy.deepcopy(node),ast.Add(),ast.Num(1))
    minus = ast.BinOp(copy.deepcopy(node),ast.Sub(),ast.Num(1))
    return Either([plus,minus])


class TrySameType(ast.NodeVisitor):

  def visit_Num(self, node):
    return AllNum()

  def visit_Name(self, node):
    return AllVar()

  def generic_visit(self, node):
    return node
