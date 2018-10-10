class BinaryOperation:
    def __init__(self, *, left_node, operator, right_node):
        self.left = left_node
        self.right = right_node

        self.op = operator
        self.token = operator


class FunctionCall:
    def __init__(self, *,
                 function_node,   # Function obj
                 args,       # list
                 modifiers,  # dict
                 flags):     # list
        self.function_node = function_node

        self.args = args
        self.modifiers = modifiers
        self.flags = flags


class Return:
    def __init__(self, token, expression):
        self.token = token
        self.expression = expression


class LoopControl:
    def __init__(self, token):
        self.token = token
        self.value = token.value


class FunctionDefinition:
    def __init__(self, *,
                 token,
                 arg_names = None,
                 arbitrary = None,
                 modifiers = None,
                 flags     = None,
                 body):
        self.token = token
        self.value = token.value
        self.arg_names = arg_names or []
        self.arbitrary = arbitrary
        self.modifiers = modifiers or {}
        self.flags = flags or []
        self.body = body


class UnaryOperation:
    def __init__(self, *, operator, expression):
        self.token = operator
        self.op = operator

        self.expression = expression


class MultipleAssign:
    def __init__(self, token, variables, arguments):
        self.token = token
        self.variables = variables
        self.arguments = arguments


class StatementList:
    def __init__(self):
        self.children = []


class Assign:
    def __init__(self, *, left_node, operator, right_node):
        self.left = left_node
        self.right = right_node

        self.op = operator
        self.token = operator


class IterableUnpacking:
    def __init__(self, token, expression):
        self.token = token
        self.expression = expression


class AttributeAccess:
    def __init__(self, left_node, attribute):
        self.left = left_node
        self.attribute = attribute
        self.name = attribute.value
        self.value = self.name


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


class WhileLoop:
    def __init__(self, *, token, expression, block):
        self.token = token
        self.expression = expression
        self.block = block


class UntilLoop(WhileLoop):
    def __init__(self, *, token, expression, block):
        super(UntilLoop, self).__init__(token=token,
                                        expression=expression,
                                        block=block)


class ForLoop:
    def __init__(self, *, token, parameters, iterable, block):
        self.token = token
        self.parameters = parameters
        self.iterable = iterable
        self.block = block


class Empty:
    pass
