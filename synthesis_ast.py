import ast, copy
from print_visitor import PrintVisitor

class Either(ast.AST):
  _fields = ['choices','id','lineno','col_offset']
  count = 0

  def __init__(self,choices):
    self.choices = choices
    self.id = Either.count
    self.lineno = 0
    self.col_offset = 0
    Either.count = Either.count + 1

  def update(self, choices):
    self.choices = choices

class AllNum(ast.AST):
  _fields = ['id','lineno','col_offset']
  count = 0

  def __init__(self):
    self.id = AllNum.count
    self.lineno = 0
    self.col_offset = 0
    AllNum.count = AllNum.count + 1

class AllVar(ast.AST):
  _fields = ['id','lineno','col_offset']
  count = 0

  def __init__(self):
    self.id = AllVar.count
    self.lineno = 0
    self.col_offset = 0
    AllVar.count = AllVar.count + 1

class AllNumVar(ast.AST):
  _fields = ['id','lineno','col_offset']
  count = 0

  def __init__(self):
    self.id = AllNumVar.count
    self.lineno = 0
    self.col_offset = 0
    AllNumVar.count = AllNumVar.count + 1

if __name__ == '__main__':
  tree = Either([AllNum(), AllVar()])
  PrintVisitor().visit(tree)
