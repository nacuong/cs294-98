import ast, sys, json, getopt, subprocess
import json, copy
from define_visitor import DefineVisitor
from return_visitor import ReturnVisitor
from param_visitor import ParamVisitor
from print_visitor import PrintVisitor
from mutate_visitor import MutateVisitor
from source_visitor import SourceVisitor
from mutator import OffByOne, TrySameType, PreserveStructure, PreserveStructureAndOp
from synthesis_visitor import SynthesisVisitor
from optparse import OptionParser
from multiprocessing import Process, Queue

t_py = None
t_rkt = None
t_ast = None

s_py = None
s_rkt = None
s_ast = None

main_func = None
lb = -10
ub = 10
array = None

debug = True

class JSONVisitorException(Exception):
  pass

class RacketVisitor(ast.NodeVisitor):
  indent = 0
  test = True
  racket = ""
  rkt_lineno = 5
  func_node = None
  rkt_col_offset = 1
  rkttopy_loc = {}
  _vid = 0
  _nid = 0
  _vnid = 0
  _cid = 0

  def __init__(self, debug, synthesis, main):
    self.debug = debug
    self.synthesis = synthesis
    self.main = main

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
      return "quotient" # TODO
    elif isinstance(op, ast.Mod):
      return "remainder"
    elif isinstance(op, ast.Pow):
      return "expt"
    elif isinstance(op, ast.Eq):
      return "equal?"
    elif isinstance(op, ast.NotEq):
      return "(lambda (x y) (not (equal? x y)))"
    elif isinstance(op, ast.Lt):
      return "<"
    elif isinstance(op, ast.LtE):
      return "<="
    elif isinstance(op, ast.Gt):
      return ">"
    elif isinstance(op, ast.GtE):
      return ">="
    elif isinstance(op, ast.FloorDiv):
      return "quotient"
    else:
      raise JSONVisitorException("Unexpected error: Missed case: %s." % op)

  """
  A visitor for allnumvar expression. Generator for synthesis, do not need to
  track line and column number.
  """
  def visit_AllNumVar(self, node):
    self.output(" (?? _vn" + str(self._vnid) + " _vv" + str(self._vnid) + " _nn" + str(self._vnid) + " ) ")
    self._vnid += 1

    self.indent_print(self.__class__.__name__ + ":")
    self.indent = self.indent + 1

    for field, value in ast.iter_fields(node):
      self.print_field_value(field, value)

    self.indent = self.indent - 1

  """
  A visitor for allvar expression. Generator for synthesis, do not need to
  track line and column number.
  """
  def visit_AllVar(self, node):
    self.output(" (v? _v" + str(self._vid) + ") ")
    self._vid += 1

    self.indent_print(self.__class__.__name__ + ":")
    self.indent = self.indent + 1

    for field, value in ast.iter_fields(node):
      self.print_field_value(field, value)

    self.indent = self.indent - 1

  """
  A visitor for allnum expression. Generator for synthesis, do not need to
  track line and column number.
  """
  def visit_AllNum(self, node):
    self.output(" (n? _n" + str(self._nid) + ") ")
    self._nid += 1

    self.indent_print(self.__class__.__name__ + ":")
    self.indent = self.indent + 1

    for field, value in ast.iter_fields(node):
      self.print_field_value(field, value)

    self.indent = self.indent - 1

  """
  A visitor for either expression. Generator for synthesis, do not need to
  track line and column number.

  """
  def visit_Either(self, node):
    self.output(" (either _c" + str(self._cid) + " ")
    self._cid += 1
    self.indent_print(self.__class__.__name__ + ":")
    self.indent = self.indent + 1
    cache_vid = self._vid
    cache_nid = self._nid
    cache_vnid = self._vnid
    max_vid, max_nid, max_vnid = 0, 0, 0

    for field, value in ast.iter_fields(node):
      if field == "choices":
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        for choice in value:
          max_vid = max(max_vid, self._vid)
          max_nid = max(max_nid, self._nid)
          max_vnid = max(max_vnid, self._vnid)

          self._vid = cache_vid
          self._nid = cache_nid
          self._vnid = cache_vnid

          self.indent_print(choice.__class__.__name__ + ":")
          self.indent = self.indent + 1
          self.visit(choice)
          self.indent = self.indent - 1
        self.indent = self.indent - 1 
      else:
        self.print_field_value(field, value)

    self._vid = max_vid
    self._nid = max_nid
    self._vnid = max_vnid

    self.indent = self.indent - 1
    self.outputln(")")

  """
  A visitor for num expression
  """
  def visit_Num(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "n":
        self.indent_print(field + ":" + str(value))

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

    self._output("(")
    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (comparators.lineno, comparators.col_offset - 1)
    self._output(self.op_to_string(ops))

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
        self.newline()
      elif field == "body":
        self.outputln("(begin")
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit_list(value)
        # for stmt in value:
        #   self.indent_print(stmt.__class__.__name__ + ":")
        #   self.indent = self.indent + 1
        #   self.visit(stmt)
        #   self.indent = self.indent - 1
        self.indent = self.indent - 1
        self.outputln(")")
      elif field == "orelse":
        self.outputln("(begin")
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit_list(value)
        # for stmt in value:
        #   self.indent_print(stmt.__class__.__name__ + ":")
        #   self.indent = self.indent + 1
        #   self.visit(stmt)
        #   self.indent = self.indent - 1
        self.indent = self.indent - 1
        self.outputln(")")
      else:
        self.print_field_value(field, value)

    self.outputln(")")

  """
  A visitor for call expression
  """
  def visit_Call(self, node):

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    # self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    func = None
    args = None
    
    for field, value in ast.iter_fields(node):
      if field == "func":
        func = value
      elif field == "args":
        args = value

    if func.__class__.__name__ == "Attribute":
      # Attribute
      self.indent_print("Attribute:")
      self.indent = self.indent + 1
      self.indent_print("attr: " + func.attr)
      if func.attr == "append":
        self.output("(set!")

        self.indent_print("value:")
        self.indent = self.indent + 1
        self.visit(func.value)
        self.indent = self.indent - 1

        self.output(" (cons")
        self.indent_print("args:")
        self.indent = self.indent + 1
        for arg in args:
          self.indent = self.indent + 1
          self.indent_print(arg.__class__.__name__ + ":")
          self.visit(arg)
          self.indent = self.indent - 1
        self.indent = self.indent - 1

        self.output(" ")
        self.indent_print("value:")
        self.indent = self.indent + 1
        self.visit(func.value)
        self.indent = self.indent - 1

        self.outputln("))")
      else:
        raise JSONVisitorException("Unexpected error: Missed case attribute: %s." % func.attr)
      self.indent = self.indent + 1
    else:
      self.output(" (")

      # name
      self.indent_print("func:")
      self.indent = self.indent + 1
      self.visit(func)
      self.indent = self.indent - 1

      # args
      self.indent_print("args:")
      self.indent = self.indent + 1
      for arg in args:
        self.indent = self.indent + 1
        self.indent_print(arg.__class__.__name__ + ":")
        self.visit(arg)
        self.indent = self.indent - 1
      self.indent = self.indent - 1

      self.output(")")

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
    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (right.lineno, right.col_offset - 1) # TODO: check
    self.output(self.op_to_string(op))

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
    
    self.indent_print("Assign:")
    self.indent = self.indent + 1

    for field, value in ast.iter_fields(node):
      if field == "targets":
        lhs = value[0]
      elif field == "value":
        rhs = value
      else:
        self.print_field_value(field, value)
        raise JSONVisitorException("Unexpected error: Missed case: %s." % value)

    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)

    if isinstance(lhs, ast.Name):
      self.output("(set!")
      self.indent_print("lhs:")
      self.indent = self.indent + 1
      self.visit(lhs)
      self.indent = self.indent - 1

      self.indent_print("rhs:")
      self.indent = self.indent + 1
      self.visit(rhs)
      self.indent = self.indent - 1
      self.outputln(")")
    elif isinstance(lhs, ast.Subscript):
      self.output("(set!")
      self.indent_print("lhs:")
      self.indent = self.indent + 1
      self.visit(lhs.value)

      self.output(" (list-set")
      self.visit(lhs.value)
      self.visit(lhs.slice)
      self.indent = self.indent - 1

      self.indent_print("rhs:")
      self.indent = self.indent + 1
      self.visit(rhs)
      self.indent = self.indent - 1
      self.output("))")
    elif isinstance(lhs, ast.Tuple):
      index = 0
      self.outputln("(let (")
      for r in rhs.elts:
        self.output("[~temp" + str(index))
        self.visit(r)
        self.outputln("]")
        index = index + 1
      self.outputln(")")
      
      index = 0
      for l in lhs.elts:
        self.output("(set!")
        self.visit(l)
        self.outputln(" ~temp" + str(index) + ")")
        index = index + 1
      self.outputln(")")
    else:
      raise JSONVisitorException("Unexpected error: Missed case Assign lhs: %s." % lha)

    self.indent = self.indent - 1

  def visit_AugAssign(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    # TODO: check
    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    
    target = None
    op = None
    val = None
    
    self.indent_print("AugAssign: (line,col) = (" + str(node.lineno) + "," + str (node.col_offset) + ")")
    self.indent = self.indent + 1
    for field, value in ast.iter_fields(node):
      if field == "target":
        target = value
      elif field == "op":
        op = value
      elif field == "value":
        val = value

    self.output("(set!")

    self.indent_print("target:")
    self.indent = self.indent + 1
    self.visit(target)
    self.indent = self.indent - 1

    self.output(" (")
    self.indent_print("op:")
    self.indent = self.indent + 1
    self.indent_print(op.__class__.__name__ + ":")
    self.indent = self.indent - 1
    self.output(self.op_to_string(op))

    self.indent_print("target:")
    self.indent = self.indent + 1
    self.visit(target)
    self.indent = self.indent - 1

    self.indent_print("value:")
    self.indent = self.indent + 1
    self.visit(val)
    self.indent = self.indent - 1

    self.outputln("))")
    self.indent = self.indent - 1
      
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
        self.output("(set! _ret")
        self.id_open(value)
        self.visit(value)
        self.id_close(value)
        self.outputln(")")
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

    self.indent = self.indent + 1
    self.indent_print("(line,col): (" + str(node.lineno) + "," + str(node.col_offset) + ")")
    self.indent = self.indent - 1

    for field, value in ast.iter_fields(node):
      if field == "id":
        if "racket" in node.__dict__:
          name = node.racket
        else:
          name = value
        self.indent = self.indent + 1
        self.indent_print(field + ":" + name)
        self.indent = self.indent - 1
        self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
        self._output(name)

  def visit_List(self,node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    self.output(" (list")
    for field, value in ast.iter_fields(node):
      self.indent = self.indent + 1
      self.indent_print(field + ":")
      if field == "elts":
        for v in value:
          self.visit(v)
      self.indent = self.indent - 1
    self.output(")")

  def visit_Subscript(self,node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset
    self.rkttopy_loc[(self.rkt_lineno, self.rkt_col_offset)] = (node.lineno, node.col_offset)
    
    for field, value in ast.iter_fields(node):
      self.indent = self.indent + 1
      self.indent_print(field + ":")
      if field == "value":
        self.output(" (list-ref")
        self.visit(value)
      elif field == "slice":
        self.visit(value)
        self.output(")")
      self.indent = self.indent - 1

  """
  A visitor for while statement
  """
  def visit_While(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    self.output("(while ")

    for field, value in ast.iter_fields(node):
      # print "while field: ", field, " value: ", value
      self.indent_print(field + ":")
      self.indent = self.indent + 1
      if field == "test":
        self.visit(value)
        self.newline()
      elif field == "body":
        self.visit_list(value)
      self.indent = self.indent - 1

    self.outputln(")")

  def visit_For(self, node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    self.output("(for ([")

    for field, value in ast.iter_fields(node):
      self.indent_print(field + ":")
      self.indent = self.indent + 1
      if field == "target":
        self.visit(value)
      elif field == "iter":
        if isinstance(value,ast.Call) and value.func.id == "range":
          self.indent_print("range:")
          self.indent = self.indent + 1
          self.output(" (in-range")
          for arg in value.args:
            self.visit(arg)
          self.indent = self.indent - 1
          self.output(")")
        else:
          self.visit(value)
        self.outputln("])")
      elif field == "body":
        self.visit_list(value)
      self.indent = self.indent - 1

    self.outputln(")")
    

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
    self.func_node = node
    self._vnid = 0 
    self._vid = 0
    self._nid = 0
    self._cid = 0

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      if field == "name":
        name = value
        if name == self.main:
          if self.debug or self.synthesis:
            name = name + "_s"
          else:
            name = name + "_t"
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
        if self.synthesis:
          # all var
          self.outputln("\t(define (v? v)")
          self.outputln("\t\t(cond")
          count = 0
          for var in node.define:
            self.outputln("\t\t\t[(= v " + str(count) +") " + var + "]") 
            count += 1
          self.outputln("\t))")

          # all var num
          self.outputln("\t(define (v?? vv)")
          self.outputln("\t\t(cond")
          count = 0
          for var in node.define:
            self.outputln("\t\t\t[(= vv " + str(count) +") " + var + "]") 
            count += 1
          self.outputln("\t))")

          # all var num
          self.outputln("\t(define (?? vn v n)")
          self.outputln("\t\t(if vn (v?? v) (n?? n)))\n")

          # allvarnum and either
          self.outputln("(define-symbolic _vn0 _vn1 _vn2 _vn3 _vn4 _vn5 _vn6 _vn7 _vn8 _vn9 _vn10 boolean?)")
          self.outputln("(define-symbolic _vv0 _vv1 _vv2 _vv3 _vv4 _vv5 _vv6 _vv7 _vv8 _vv9 _vv10 number?)")
          self.outputln("(define-symbolic _nn0 _nn1 _nn2 _nn3 _nn4 _nn5 _nn6 _nn7 _nn8 _nn9 _nn10 number?)")
          self.outputln("(define-symbolic _n0 _n1 _n2 _n3 _n4 _n5 _n6 _n7 _n8 _n9 _n10 number?)")
          self.outputln("(define-symbolic _v0 _v1 _v2 _v3 _v4 _v5 _v6 _v7 _v8 _v9 _v10 number?)")
          self.outputln("")
          self.outputln("(define-symbolic _c0 _c1 _c2 _c3 _c4 _c5 _c6 _c7 _c8 _c9 _c10 number?)")
          self.outputln("")

        self.outputln("(define _ret `none)")
        for var in node.define:
          if node.define[var] == "var":
            self.outputln("(define " + var + " #f)")
      elif field == "body":
        body = value
        self.indent_print(field + ":")
        self.indent = self.indent + 1
        self.visit_list(value)
        # for stmt in body:
        #   self.indent_print(stmt.__class__.__name__ + ":")
        #   self.indent = self.indent + 1
        #   self.visit(stmt)
        #   self.indent = self.indent - 1
        self.indent = self.indent - 1
      elif field == "decorator_list":
        decorator_list = value
        self.print_field_value(field, value)
     
    self.outputln("(if (equal? _ret `none) (void) _ret))")

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

  def visit_Load(self,node):
    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset
    print "Load", node.__dict__

    for field, value in ast.iter_fields(node):
      print "Load: field = ", field, value

  def visit_list(self, node):
    if len(node) == 0:
      self.outputln("(void)")
      return

    count = 0
    for item in node:
      self.indent_print(item.__class__.__name__ + ":")
      self.indent = self.indent + 1
      if isinstance(item, ast.AST):
        if "scope" in item.__dict__:
          count += 1
          self.outputln("(when (equal? _ret `none)")
        self.visit(item)
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s." % item)
      self.indent = self.indent - 1

    for i in xrange(count):
      self.output(")")
    self.newline()

  """
  Generic visitor for Python program. Syntax-directed translation to racket.
  Return the racket program and the mapping from (line, col) of python to
  (line, col) of racket program.
  """
  def generic_visit(self, node):
    if isinstance(node, list):
      self.visit_list(node)
      return
    elif node.__class__.__name__ == "NoneType":
      self.output(" (void)")
      return
    if (not (isinstance(node, ast.AST))):
      raise JSONVisitorException("Unexpected error: Non-ast passed to visit.")

    # associate racket line and column to node
    node.rkt_lineno = self.rkt_lineno
    node.rkt_col_offset = self.rkt_col_offset

    for field, value in ast.iter_fields(node):
      # print "field: ", field, " value: ", value
      self.indent_print(field + ":")
      self.indent = self.indent + 1
      if (isinstance(value, list)):
        self.visit_list(value)
      elif isinstance(value, ast.AST):
        self.visit(value)
      else:
        raise JSONVisitorException("Unexpected error: Missed case: %s.  Please report to the TAs." % value)
      self.indent = self.indent - 1

    return (self.racket, self.rkttopy_loc)

def translate_to_racket(my_ast, rkt, debug):
  ReturnVisitor().visit(my_ast)
  DefineVisitor().visit(my_ast)
  (racket, rkttopy_loc) = RacketVisitor(debug, False, main_func).visit(my_ast)

  if debug:
    print(rkttopy_loc)

  if debug:
    print(racket)

  f = open(rkt, "w")
  f.write("#lang s-exp rosette\n")
  f.write("(require \"util.rkt\")\n")
  if debug:
    f.write("(require rosette/lang/debug)\n")
    f.write("(provide " + main_func + "_s)\n")
  else:
    f.write("(provide " + main_func + "_t)\n")
  f.write(racket)
  f.close()

  return rkttopy_loc

def get_syms(n):
  syms = ""
  for i in xrange(n):
    if i in array:
      syms += "l" + str(i) + " "
      for j in xrange(10):
        syms += "i" + str(i) + "_" + str(j) + " "
    else:
      syms += "i" + str(i) + " "

  return syms

def get_args(n):
  args = ""
  for i in xrange(n):
    if i in array:
      args += "(take (list "
      for j in xrange(10):
        args += "i" + str(i) + "_" + str(j) + " "
      args += ") l" + str(i) + ")"
    else:
      args += "i" + str(i) + " "
  return args

def get_args_cnst(n):
  args_cnst = ""
  for i in xrange(n):
    if i in array:
      for j in xrange(10):
        args_cnst += "(< i" + str(i) + "_" + str(j) + " " + str(ub) + ") "
        args_cnst += "(> i" + str(i) + "_" + str(j) + " " + str(lb) + ") "
      args_cnst += "(<= l" + str(i) + " 10) (>= l" + str(i) + " 0) "
    else:
      args_cnst += "(< i" + str(i) + " " + str(ub) + ") (> i" + str(i) + " " + str(lb) + ") "
  return args_cnst

def generate_synthesizer(my_ast, synrkt, mutation): 
  clone_ast = copy.deepcopy(my_ast)
  MutateVisitor(mutation).visit(clone_ast)
  (racket, rkttopy_loc) = RacketVisitor(False, True, main_func).visit(clone_ast)

  if (debug):
    print racket

  s_args = ParamVisitor(main_func).visit(s_ast)
  n = len(s_args)
  syms = get_syms(n)
  args = get_args(n)
  args_cnst = get_args_cnst(n)

  f = open(synrkt, "w")
  f.write("#lang s-exp rosette\n")
  f.write("(require \"util.rkt\")\n")
  f.write("(require \"../" + t_rkt + "\")\n\n")
  f.write("(define-symbolic ")
  f.write(syms)
  f.write("number?)\n")
  f.write("(configure [bitwidth 32] [loop-bound 20])\n")
  f.write("\n")
  f.write("(define-syntax-rule (either c a ...)\n")
  f.write("\t(choose c (list a ...)))\n")
  f.write("\n")
  f.write("(define (choose c lst)\n")
  f.write("\t(list-ref lst c))\n")
  f.write("\n")

  # AllNum 
  f.write("(define (n? n)\n")
  f.write("\t(assert (and (< n " + str(ub) + ") (>= n " + str(lb) + ")))\n")
  f.write("\tn)")
  f.write("\n")

  #AllVarNum
  f.write("(define (n?? nn)\n")
  f.write("\t(assert (and (< nn " + str(ub) + ") (>= nn " + str(lb) + ")))\n") 
  f.write("\tnn)")

  #The program
  f.write(racket)

  #Call synthesizer
  f.write("(define model\n")
  f.write("(synthesize\n")
  f.write("\t#:forall (list " + syms + ")\n")
  f.write("\t#:assume (assert (and " + args_cnst + "))\n")
  f.write("\t#:guarantee (assert (equal? ")
  f.write("(" + main_func + "_t " + args + ") ")
  f.write("(" + main_func + "_s " + args + ")")
  f.write("))))\n")
  f.write("\n")
  f.write("(define solution (solution->list model))\n")
  f.write("(for-each (lambda (sol)\n")
  f.write("\t(define val (cdr sol))\n")
  f.write("\t(define sym (sym-name (car sol)))\n")
  f.write("\t(define symtype (syntax->datum sym))\n")
  f.write("\t(printf \"~a:~a\\n\" symtype val))\n")
  f.write("\t solution)\n")
  f.close()

  return clone_ast

def run_synthesizer(ast, synrkt, fix, queue):
  mutated_ast = generate_synthesizer(ast, synrkt, fix)

  either = {}
  allnumvarbool = {}
  allnumvarnum = {} 
  allnumvarvar = {}
  allnum = {}
  allvar = {}
  synr_result = subprocess.check_output(["racket", synrkt], shell=False)

  if synr_result:
    for line in synr_result.split('\n'): 
      res = line.split(':')
      if res[0].startswith("_vn"):
        allnumvarbool[int(res[0].strip("_vn"))] = int(res[1])
      elif res[0].startswith("_vv"):
        allnumvarvar[int(res[0].strip("_vv"))] = int(res[1])
      elif res[0].startswith("_nn"):
        allnumvarnum[int(res[0].strip("_nn"))] = int(res[1])
      elif res[0].startswith("_c"):
        either[int(res[0].strip("_c"))] = int(res[1])
      elif res[0].startswith("_n"):
        allnum[int(res[0].strip("_n"))] = int(res[1])
      elif res[0].startswith("_v"):
        allvar[int(res[0].strip("_v"))] = int(res[1])

    #if debug:
      #print either
      #print allnum

      #print "Mutated ast:"
      #PrintVisitor().visit(mutated_ast)

    locs = []
    for loc in fix:
      locs.append(loc)
    synthesizer = SynthesisVisitor(either, allnum, allvar, locs)
    synthesizer.visit(mutated_ast)
    fixes = synthesizer.getFixes()

    queue.put(fixes)

def autograde():
  t_args = ParamVisitor(main_func).visit(t_ast)
  s_args = ParamVisitor(main_func).visit(s_ast)

  if not len(t_args) == len(s_args):
    print "Numbers of arguments to the main functions are different."
    exit()

  n = len(t_args)
  syms = get_syms(n)
  args = get_args(n)
  args_cnst = get_args_cnst(n)

  f = open("grade.rkt", "w")
  f.write("#lang s-exp rosette\n")
  f.write("(require \"" + t_rkt + "\" \"" + s_rkt + "\")\n")
  f.write("(require json rosette/lang/debug rosette/lib/tools/render)\n\n")
  f.write("(configure [bitwidth 32] [loop-bound 10])\n")

  f.write("(define-symbolic" + syms + " number?)\n")
  f.write("(define ce-model\n")
  f.write("  (verify\n")
  f.write("\t#:assume (assert (and " + args_cnst + "))\n")
  f.write("\t#:guarantee (assert (equal? ")
  f.write("(" + main_func + "_t " + args + ") ")
  f.write("(" + main_func + "_s " + args + ")")
  f.write("))))\n\n")

  concrete_args = "".join([" (evaluate i" + str(i) + " ce-model)" for i in xrange(n)])
  f.write("(define sol\n")
  f.write("  (debug [(lambda (x) (or (boolean? x) (number? x)))]\n")
  f.write("    (assert (equal? (" + main_func + "_t" + concrete_args + ") (" \
      + main_func + "_s" + concrete_args + ")))))\n")
  f.write("(define sol-list (remove-duplicates (filter-map sym-origin (core sol))))\n")
  f.write("(define return (map (lambda (item) (list " + \
      "(syntax-line item) (syntax-column item) (syntax-span item) " + \
      "(symbol->string (second (identifier-binding item))))) " + \
      "(filter syntax-line sol-list)))\n")
  f.write("(write-json return)")

def generateAllFixes(bugs, mutators): 
  fixes = []
  bug = bugs[-1]

  if len(bugs) == 1:
    for mutator in mutators:
      fix = {}
      fix[bug] = mutator
      fixes.append(fix)

    return fixes
  else:
    del bugs[-1]
    sub_fixes = generateAllFixes(bugs, mutators)
    for sub_fix in sub_fixes:
      for mutator in mutators:
        fix = copy.deepcopy(sub_fix)
        fix[bug] = mutator
        fixes.append(fix)

    return fixes

if __name__ == '__main__':

  parser = OptionParser()
  parser.add_option("-t", "--teacher-py")
  parser.add_option("-s", "--student-py")
  parser.add_option("-m", "--main")
  parser.add_option("-l", "--lower-bound", default=-10000)
  parser.add_option("-u", "--upper-bound", default=10000)
  parser.add_option("-a", "--array", default="")
  (options, args) = parser.parse_args()

  main_func = options.main
  rkttopy_loc_s = {}

  if options.teacher_py:
    t_py = options.teacher_py
    t_rkt = t_py.strip(".py") + ".rkt"
    t_ast = ast.parse(open(t_py,"r").read())
    translate_to_racket(t_ast, t_rkt, False)

  if options.student_py:
    s_py = options.student_py
    s_rkt = s_py.strip(".py") + ".rkt"
    s_ast = ast.parse(open(s_py,"r").read())
    rkttopy_loc_s = translate_to_racket(s_ast, s_rkt, True)

  if t_py and s_py:
    lb = options.lower_bound
    ub = options.upper_bound
    array = options.array.split(',')
    if len(array) == 1 and array[0] == '':
      array = []
    array = set([int(x) for x in array])
    autograde()

#  grade_result = subprocess.check_output(["racket", "grade.rkt"])
#  if debug:
#    print("Grade result from rossette:")
#    print(grade_result)

#  feedback = json.loads(grade_result)

  #
  # Generate feedback 2: location to be fixed
  #
#  print("Location in python program to be fixed:")
#  for i in xrange(len(feedback)):
#    try:
#      print("\t" + str(rkttopy_loc_s[feedback[i][0], feedback[i][1]]))
#    except:
#      print("\t Key not found: " + str(feedback[i][0]) + ", " + str(feedback[i][1]))

  #print(ast.dump(ast.parse(sys.stdin.read())))

  #
  # Generate mutated python program to racket
  #
  if options.student_py and options.teacher_py:
    s_py = options.student_py
    synrkt = s_py.strip(".py") + "_synr.rkt"
    offbyone = OffByOne()
    sametype = TrySameType()
    samestruct = PreserveStructure()

    #bugs = [(5,15), (5,18), (7,38)]
    #mutator = [offbyone, sametype, sametype]
    #bugs = [(5,15),(7,38)]
    bugs = [(4,20),(9,14)] # ComputeDeriv
    mutator = [offbyone, sametype] # ComputeDeriv
    #bugs = [(3,15), (5,15)] # hw1-4 (hailstone)
    #mutator = [offbyone, sametype] #h1-4 (hailstone)
    #bugs = [(3,13), (5, 8)] # mulIA 
    #mutator = [sametype, samestruct]
    fixes = generateAllFixes(bugs, mutator)
    queue = Queue()
    workers = []

    for i in xrange(0, len(fixes)):
      workers.append(Process(target=run_synthesizer, args=(s_ast, synrkt + "_"
        + str(i), fixes[i], queue)))

    for i in xrange(0, len(fixes)):
      workers[i].start()

    while True:
      if not queue.empty():
        # terminate all processes
        for i in xrange(0, len(fixes)):
          if workers[i].is_alive():
            workers[i].terminate()
        # display results
        fixes = queue.get()
        for fix in fixes:
          print "At line " + str(fix.lineno) + " and offset " + str(fix.col_offset) 
          print "\t " + SourceVisitor().visit(fix)
        break
