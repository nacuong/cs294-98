import ast, sys, json, getopt
from define_visitor import DefineVisitor
from param_visitor import ParamVisitor
from optparse import OptionParser

t_py = None
t_rkt = None
t_func = None
t_ast = None

s_py = None
s_rkt = None
s_func = None
s_ast = None

class JSONVisitorException(Exception):
  pass

class RacketVisitor(ast.NodeVisitor):
  indent = 0
  test = True
  racket = ""
  rkt_lineno = 5
  rkt_col_offset = 1
  rkttopy_loc = {}

  def __init__(self, debug):
    self.debug = debug

  """
  Print ast with indentation
  """
  def indent_print(self, s):
    if self.test:
      for i in xrange(0, self.indent):
        print '  ',
      print s

  def output(self, code):
    self.racket = self.racket + code
    self.rkt_col_offset += len(code)

  def _output(self, code):
    self.output(" " + code)

  def outputln(self, code):
    self.output(code)
    self.newline()

  def newline(self):
    self.racket = self.racket + "\n"
    self.rkt_lineno += 1
    self.rkt_col_offset = 1

  def id_open(self, x):
    if self.debug and (x.__class__.__name__ == "Name" or x.__class__.__name__ == "Num"):
      self._output("(")
      print(str(self.rkt_lineno) + "," + str(self.rkt_col_offset) + " : " + str(x.lineno) + "," + str(x.col_offset))
      self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (x.lineno,
          x.col_offset)
      self._output("identity ")

  def id_close(self, x):
    if self.debug and (x.__class__.__name__ == "Name" or x.__class__.__name__ == "Num"):
      self.output(")")

  """
  Print all field/value pairs with indentation
  """
  def print_field_value(self, field, value):
    self.indent_print(field + ":")
    self.indent = self.indent + 1
    self.indent_print(value)
    self.indent = self.indent - 1

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
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "n":
        self.indent = self.indent + 1
        self.indent_print(field + ":" + str(value))
        self.indent = self.indent - 1

        self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
        self._output(str(value))

  """
  A visitor for compare expression
  """
  def visit_Compare(self, node):
    left = None
    ops = None
    comparators = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "left":
        left = value
      elif field == "ops":
        ops = value[0]
      elif field == "comparators":
        comparators = value[0]
      else:
        self.print_field_value(field, value)

    # process op
    self.indent_print("ops:")
    self.indent = self.indent + 1
    self.indent_print(ops.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    self._output(" (" + self.op_to_string(ops))

    # process left
    self.indent_print("left:")
    self.indent = self.indent + 1
    self.indent_print(left.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.id_open(left)
    self.visit(left)
    self.id_close(left)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    # process comparators
    self.indent_print("comparators:")
    self.indent = self.indent + 1
    self.indent_print(comparators.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.id_open(comparators)
    self.visit(comparators)
    self.id_close(comparators)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self.output(")")


  """
  A visitor for if expression
  """
  def visit_If(self, node):

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    self.output("(if")
    for field, value in ast.iter_fields(node):
      if field == "test":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "body":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in value:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "orelse":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in value:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)

    self.newline()

  """
  A visitor for call expression
  """
  def visit_Call(self, node):

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    # self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)

    self.output("(")
    for field, value in ast.iter_fields(node):
      if field == "func":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.visit(value)
        self.indent = self.indent - 1
      elif field == "args":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for arg in value:
          self.indent_print(arg.__class__.__name__ + ":")
          self.visit(arg)
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)
    self.outputln(")")

  """
  A visitor for binop expression
  """
  def visit_BinOp(self, node):
    left = None
    op = None
    right = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "left":
        left = value
      elif field == "op":
        op = value
      elif field == "right":
        right = value
      else:
        self.print_field_value(field, value)

    # process op
    self.indent_print("op:")
    self.indent = self.indent + 1
    self.indent_print(op.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self._output("(")
    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (right.lineno, right.col_offset - 1)
    self._output(self.op_to_string(op))

    # process left
    self.indent_print("left:")
    self.indent = self.indent + 1
    self.indent_print(left.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.id_open(left)
    self.visit(left)
    self.id_close(left)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    # process right
    self.indent_print("right:")
    self.indent = self.indent + 1
    self.indent_print(right.__class__.__name__ + ":")
    self.indent = self.indent + 1
    self.id_open(right)
    self.visit(right)
    self.id_close(right)
    self.indent = self.indent - 1
    self.indent = self.indent - 1

    self.output(")")

  """
  A visitor for assign expression
  """
  def visit_Assign(self, node):
    lhs = None
    rhs = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "targets":
        lhs = value[0]
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value[0].__class__.__name__ + ":")
        self.indent = self.indent - 1
      elif field == "value":
        rhs = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        # self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1
      else:
        self.print_field_value(field, value)
        raise JSONVisitorException("Unexpected error: Missed case: %s." % value)

    #print lhs, isinstance(lhs, ast.Name)
    if isinstance(lhs, ast.Name):
      self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
      self.output("(set!")
      self.visit(lhs)
      self.visit(rhs)
      self.outputln(")")
    elif isinstance(lhs, ast.Tuple):
      for l,r in zip(lhs.elts, rhs.elts):
        self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
        self.output("(set!")
        self.visit(l)
        self.visit(r)
        self.outputln(")")

  """
  A visitor for return expression
  """
  def visit_Return(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "value":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.indent_print(value.__class__.__name__ + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.indent = self.indent - 1

  """
  A visitor for name expression
  """
  def visit_Name(self, node):
    name = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "id":
        if "racket" in node.__dict__:
          name = node.racket
        else:
          name = value
        self.indent = self.indent + 1
        self.indent_print(field + ":" + name)
        self.indent = self.indent - 1

        print(str(self.rkt_lineno) + "," + str(self.rkt_col_offset) + " : " + str(node.lineno) + "," + str(node.col_offset) + " : " + name)
        self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
        self._output(name)

  """
  A visitor for function arguments.
  """
  def visit_arguments(self, node):
    args = None
    vararg = None
    kwarg = None
    defaults = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "args":
        args = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for arg in args:
          self.indent_print(arg.__class__.__name__ + ":")
          self.visit(arg)
        self.indent = self.indent - 1
      elif field == "vararg":
        vararg = value
        self.print_field_value(field, value)
      elif field == "kwarg":
        kwarg = value
        self.print_field_value(field, value)
      elif field == "defaults":
        defaults = value
        self.print_field_value(field, value)

      if vararg or kwarg or defaults:
        raise JSONVisitorException("Unexpected error: Missed case: vararg, kwarg or defaults is not empty.  Please report to the TAs.")

  """
  A visitor for function definition.
  """
  def visit_FunctionDef(self, node):
    name = None
    args = None
    body = None
    decorator_list = None

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "name":
        name = value
        self.print_field_value(field, value)
        # declare a function with name
        if self.debug:
          self.newline()
          self.output("(define/debug (" + name)
        else: 
          self.newline()
          self.output("(define (" + name)
      elif field == "args":
        args = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit(value)
        self.indent = self.indent - 1
        self.outputln(")")
        for var in node.define:
          if node.define[var] == "var":
            self.outputln("(define " + var + " #f)")
      elif field == "body":
        body = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for stmt in body:
          self.indent_print(stmt.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(stmt)
          self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "decorator_list":
        decorator_list = value
        self.print_field_value(field, value)
     
    self.outputln(")")

    if decorator_list:
      raise JSONVisitorException("Unexpected error: Missed case: decorator_list is not empty.")

  """
  A visitor for module.
  """
  def visit_Module(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    # construct variable definition in racket
    for var in node.define:
      if node.define[var] == "var":
        self.outputln("(define " + var + " #f)")

    return self.generic_visit(node)

  """
  Generic visitor for Python program. Syntax-directed translation to racket.
  Return the racket program and the mapping from (line, col) of python to
  (line, col) of racket program.
  """
  def generic_visit(self, node):
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.  Please report to the TAs.")

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      print "field: ", field, " value: ", value
      self.indent_print(field + ":")
      self.indent = self.indent + 1
      if (isinstance(value, list)):
        for item in value:
          if isinstance(item, ast.AST):
            self.visit(item)
          else:
            raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % item)
      elif isinstance(value, ast.AST):
        self.visit(value)
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)
      self.indent = self.indent - 1

    return (self.racket, self.rkttopy_loc)

def translate_to_racket(my_ast, rkt, debug):
  DefineVisitor().visit(my_ast)
  (racket, rkttopy_loc) = RacketVisitor(debug).visit(my_ast)

  print(rkttopy_loc)

  print(racket)
  f = open(rkt, "w")
  f.write("#lang s-exp rosette\n")
  f.write("(require \"util.rkt\")\n")
  if debug:
    f.write("(require rosette/lang/debug)\n")
  f.write("(provide (all-defined-out))\n")
  f.write(racket)
  f.close()


def autograde():
  t_args = ParamVisitor(t_func).visit(t_ast)
  s_args = ParamVisitor(s_func).visit(s_ast)

  if not len(t_args) == len(s_args):
    print "Numbers of arguments to the main functions are different."
    exit()

  n = len(t_args)

  f = open("grade.rkt", "w")
  f.write("#lang s-exp rosette\n")
  f.write("(require \"" + t_rkt + "\" \"" + s_rkt + "\")\n")
  f.write("(require json rosette/lang/debug)\n\n")
  f.write("(configure [bitwidth 32] [loop-bound 10])\n")

  args = "".join([" i" + str(i) for i in xrange(n)])
  f.write("(define-symbolic" + args + " number?)\n")
  f.write("(define ce-model\n")
  f.write("  (verify\n")
  f.write("   #:assume (assert (and " \
            + " ".join(["(< i" + str(i) + " 10000) (>= i" + str(i) + " -10000)" \
                          for i in xrange(n)]) \
            + "))\n")
  f.write("   #:guarantee (assert (eq? (" + t_func + args + ") (" + s_func + args + ")))))\n\n")

  concrete_args = "".join([" (evaluate i" + str(i) + " ce-model)" for i in xrange(n)])
  f.write("(define sol\n")
  f.write("  (debug [(lambda (x) (or (boolean? x) (number? x)))]\n")
  f.write("    (assert (eq? (" + t_func + concrete_args + ") (" \
            + s_func + concrete_args + ")))))\n")
  f.write("(define sol-list (remove-duplicates (filter-map sym-origin (core sol))))\n")
  f.write("(define return (map (lambda (item) (list " + \
            "(syntax-line item) (syntax-column item) (syntax-span item) " + \
            "(symbol->string (second (identifier-binding item))))) " + \
            "(filter syntax-line sol-list)))\n")
  f.write("(write-json return)")
                         

if __name__ == '__main__':

  parser = OptionParser()
  parser.add_option("-a", "--teacher-py")
  parser.add_option("-b", "--teacher-func")
  parser.add_option("-x", "--student-py")
  parser.add_option("-y", "--student-func")
  (options, args) = parser.parse_args()

  if options.teacher_py:
    t_py = options.teacher_py
    t_rkt = t_py.strip(".py") + ".rkt"
    t_ast = ast.parse(open(t_py,"r").read())
    translate_to_racket(t_ast, t_rkt, False)

  if options.student_py:
    s_py = options.student_py
    s_rkt = s_py.strip(".py") + ".rkt"
    s_ast = ast.parse(open(s_py,"r").read())
    translate_to_racket(s_ast, s_rkt, True)

  if t_py and s_py and options.teacher_func and options.student_func:
    t_func = options.teacher_func
    s_func = options.student_func
    autograde()
    

  #print(ast.dump(ast.parse(sys.stdin.read())))

