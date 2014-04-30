import ast, sys
from print_visitor import PrintVisitor

class JSONVisitorException(Exception):
  pass

class ReturnVisitor(ast.NodeVisitor):

  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    has_return = False

    for field, value in ast.iter_fields(node):
      if field == "body" and isinstance(value, list):
        l = []
        ret = False
        for item in value:
          if ret:
            item.scope = True
            print item

          if isinstance(item, ast.Return):
            ret = self.visit(item)
            l.append(item)
            has_return = True
            break
          elif isinstance(item, ast.AST):
            ret = self.visit(item)
            l.append(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
        node.body = l
        
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, ast.AST):
            ret = self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)

    return has_return

if __name__ == '__main__':
  my_ast = ast.parse(sys.stdin.read())
  PrintVisitor().visit(my_ast)
  print "--------------------------------------"
  ReturnVisitor().visit(my_ast)
  PrintVisitor().visit(my_ast)
