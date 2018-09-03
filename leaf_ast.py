"""Classes for AST building."""

__all__ = [
    'NodeParser',

    'BinaryOperation',
    'UnaryOperation',
    'FunctionCall',
    'Variable',
    'StatementList',
    'Assign',
    'Empty'
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
                 modifiers): # dict
        self.function = function
        self.args = args
        self.modifiers = modifiers 


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
