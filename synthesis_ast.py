import ast, copy
from print_visitor import PrintVisitor

class Either(ast.AST):
  _fields = ['choices','id']
  count = 0

  def __init__(self,choices):
    self.choices = choices
    self.id = Either.count
    Either.count = Either.count + 1

class AllNum(ast.AST):
  _fields = ['id']
  count = 0

  def __init__(self):
    self.id = AllNum.count
    AllNum.count = AllNum.count + 1

class AllVar(ast.AST):
  _fields = ['id']
  count = 0

  def __init__(self):
    self.id = AllVar.count
    AllVar.count = AllVar.count + 1

class AllNumVar(ast.AST):
  _fields = ['id']
  count = 0

  def __init__(self):
    self.id = AllNumVar.count
    AllNumVar.count = AllNumVar.count + 1

if __name__ == '__main__':
  tree = Either([AllNum(), AllVar()])
  PrintVisitor().visit(tree)
