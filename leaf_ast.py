"""Classes for AST building."""

__all__ = [
    'NodeParser',

    'BinaryOperation',
    'UnaryOperation',
    'FunctionCall',
    'Variable',
    'StatementList',
    'Assign',
    'IfStatement',
    'Empty',
    ]


class BinaryOperation:
    def __init__(self, *, left_node, operator, right_node):
        self.left = left_node
        self.right = right_node

        self.op = operator
        self.token = operator


class FunctionCall:
    def __init__(self, *,
                 function,   # Function obj
                 args,       # list
                 modifiers,  # dict
                 flags):     # list
        self.function = function
        self.args = args
        self.modifiers = modifiers
        self.flags = flags

    def __str__(self):
        return self.function.name


class UnaryOperation:
    def __init__(self, *, operator, expression):
        self.token = operator
        self.op = operator

        self.expression = expression


class StatementList:
    def __init__(self):
        self.children = []


class Assign:
    def __init__(self, *, left_node, operator, right_node):
        self.left = left_node
        self.right = right_node

        self.op = operator
        self.token = operator


class Variable:
    def __init__(self, token):
        self.token = token
        self.value = token.value


class IfStatement:
    def __init__(self, *, token, expression,
                                 block,
                                 elif_expressions=None,
                                 elif_blocks=None,
                                 else_block=None):
        self.token = token

        self.expression = expression
        self.block = block

        self.elif_expressions = elif_expressions
        self.elif_blocks = elif_blocks

        self.else_block = else_block


class Empty:
    pass


# Node Pasring

class NodeParser:
    def parse(self, node):
        method = 'parse_{}'.format(node.__class__.__name__)
        parser = getattr(self, method, self.parsing_error)
        return parser(node)

    def parsing_error(self, node):
        raise TypeError('Couldn\'t find parse_{} method'
                        .format(node.__class__.__name__))
