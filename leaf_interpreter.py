"""AST Interpreter for Leaf."""

import sys
import decimal

from leaf_types import *
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
            return self.parse_ShowFunction(node)

        elif node.function.name == JOIN:
            return self.parse_JoinFunction(node)

        elif node.function.name == STR_FUNC:
            return self.parse_StrFunction(node)

        elif node.function.name == NUM_FUNC:
            return self.parse_NumFunction(node)

        else:
            raise Exception('Unsupported function call {}'
                            .format(node.function.name))

    def parse_ShowFunction(self, node):
        end = str(node.modifiers.get('end', '\n'))  # default newline \n
        sep = str(node.modifiers.get('sep', ' '))   # default space char
        for flag in node.flags:
            if flag == 'comma_sep':
                sep = ', '
            elif flag == 'no_newline':
                end = ''
            else:
                self.unexpected_flag(flag)

        for arg in node.args[:-1]:
            val = self.parse(arg)
            sys.stdout.write(str(val) + sep)  # add sep char

        val = self.parse(node.args[-1])
        sys.stdout.write(str(val) + end)  # add end char

    def parse_JoinFunction(self, node):
        start = str(node.modifiers.get('start', ''))  # default none
        sep = str(node.modifiers.get('sep', ''))      # default none
        end = str(node.modifiers.get('end', ''))      # default none
        for flag in node.flags:
            if flag == 'comma_sep':
                sep = ', '
            else:
                self.unexpected_flag(flag)

        result = start
        for arg in node.args:
            result += sep + str(self.parse(arg))
        result += end

        return String(Token(STR, result))

    def parse_StrFunction(self, node):
        return String(Token(STR, str(self.parse(node.args[0]))))

    def parse_NumFunction(self, node):
        result = ''   # similar to lexer here to check for a num format
        string = self.parse(node.args[0])
        if isinstance(string, Number):
            return Number(Token(NUM, decimal.Decimal(float(string))))
        length = len(string)
        pos = 0
        while pos < length and string[pos] in digits:
            result += string[pos]
            pos += 1
        if pos < length and string[pos] == '.':
            result += string[pos]
            pos +=1

        while pos < length and string[pos] in digits:
            result += string[pos]
            pos += 1

        return Number(Token(NUM, decimal.Decimal(result)))


    def parse_Number(self, node):
        return node   # return the Number object itself, as this will
                      # handle the arithmetic/comparisons on its own

    def parse_String(self, node):
        return node   # return the String object itself so that
                      # its own internal methods can handle operations

    def parse_Boolean(self, node):
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

    def parse_IfStatement(self, node):
        if bool(self.parse(node.expression)):
            self.parse(node.block)
            return   # discard any more clauses

        if node.elif_expressions:
            for expr, block in zip(node.elif_expressions,
                                   node.elif_blocks):
                if bool(self.parse(expr)):
                    self.parse(block)
                    return  # discard any more elif/else clauses

        if node.else_block:
            self.parse(node.else_block)

    def parse_Empty(self, node):
        return None

    def parse_Assign(self, node):
        name = node.left.value
        self.GLOBAL_SCOPE[name] = self.parse(node.right)

    def parse_Variable(self, node):
        name = node.value
        try:
            value = self.GLOBAL_SCOPE[name]
        except KeyError:
            raise NameError("Could not find variable {}"
                            .format(repr(name)))
        else:
            return value

    def unexpected_flag(self, flag):
        raise SyntaxError('unexpected flag {}'.format(flag))
