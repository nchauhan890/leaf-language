"""AST Interpreter for Leaf."""

import sys

from tokens import *
from leaf_ast import NodeParser


class Interpreter(NodeParser):

    def __init__(self, parser):
        self.parser = parser
        self.GLOBAL_SCOPE = {}

    def interpret(self):
        self.abstract_syntax_tree = self.parser.parse()
        return self.parse(self.abstract_syntax_tree)

    def parse_BinaryOperation(self, node):
        operator = node.op
        ###### semantic check left and right types #####
        if operator.type == ADD:
            return self.parse(node.left) + self.parse(node.right)

        elif operator.type == SUB:
            return self.parse(node.left) - self.parse(node.right)

        elif operator.type == MUL:
            return self.parse(node.left) * self.parse(node.right)

        elif operator.type == FLOORDIV:  # floor div
            return self.parse(node.left) // self.parse(node.right)

        elif operator.type == DIV:       # normal div
            return self.parse(node.left) / self.parse(node.right)


        elif operator.type == POWER:
            return self.parse(node.left) ** self.parse(node.right)


        elif operator.type == EQUAL:
            return self.parse(node.left) == self.parse(node.right)

        elif operator.type == N_EQUAL:
            return self.parse(node.left) != self.parse(node.right)

        elif operator.type == L_EQUAL:
            return self.parse(node.left) <= self.parse(node.right)

        elif operator.type == G_EQUAL:
            return self.parse(node.left) >= self.parse(node.right)

        elif operator.type == LESS:
            return self.parse(node.left) < self.parse(node.right)

        elif operator.type == GREATER:
            return self.parse(node.left) > self.parse(node.right)

        else:
            raise Exception('Could not parse binary operation')

    def parse_FunctionCall(self, node):
        if node.function.name == SHOW:
            end = node.modifiers.get('end', '\n')  # default newline \n
            ###### semantic check for string ######
            for arg in node.args:
                sys.stdout.write(str(self.parse(arg)) + end)

        else:
            raise Exception('Could not parse function call')

    def parse_Number(self, node):
        return node   # return the Number object itself, as this will
                      # handle the arithmetic/comparisons on its own

    def parse_String(self, node):
        return node   # return the String object itself so that
                      # its own internal methods can handle operations

    def parse_UnaryOperation(self, node):
        operator = node.op.type
        if operator == ADD:
            return +self.parse(node.expression)
        
        elif operator == SUB:
            return -self.parse(node.expression)

        else:
            raise Exception('Could not parse unary operation')

    def parse_StatementList(self, node):
        for child in node.children:
            # print(self.parse(child))
            self.parse(child)

    def parse_Empty(self, node):
        pass

    def parse_Assign(self, node):
        name = node.left.value
        self.GLOBAL_SCOPE[name] = self.parse(node.right)

    def parse_Variable(self, node):
        name = node.value
        value = self.GLOBAL_SCOPE.get(name)
        if value is None:
            raise NameError("Could not find variable {}"
                            .format(repr(name)))
        else:
            return value
