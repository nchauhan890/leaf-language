"""Parser for Leaf."""

from leaf_types import *
from leaf_ast import *


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.next_token()
        self.seen_variables = []  # temporary store of used variable names
        self.indentation_level = 0
        self.buffer = []

    def lookahead(self, n=1):
        while len(self.buffer) < n:
            self.buffer.append(self.next_token())
        return self.buffer[n - 1]

    def next_token(self):
        if self.buffer:
            return self.buffer.pop(0)
        else:
            return self.lexer.next_token()

    def consume_token(self, token_type):
        if self.current_token.type == token_type:
            # print('                  old token', self.current_token)
            self.current_token = self.next_token()
            # print('                  new token', self.current_token)
        else:
            self.raise_error(token_type=token_type,
                             received=self.current_token.type)
        # print(self.current_token, end='')

    def raise_error(self, token=None, *, token_type=None, received=None):
        # print('CURRENT TOKEN:', self.current_token)
        # print('indentation_level', self.indentation_level)
        if token:
            raise SyntaxError('Invalid syntax: {} ({})'
                              .format(str(token.value), token.type))
        elif token_type and received:
            raise SyntaxError('Invalid syntax: expected {}, got {}'
                              .format(token_type, received))
        else:
            raise SyntaxError('Invalid syntax')

    def program(self):
        return self.statement_list()

##    def compound_statement(self):
##        root = CompoundStatement()
##        for node in self.statement_list():
##            root.children.append(node)
##
##        return root

    def statement_list(self):
        root = StatementList()
        root.children.append(self.statement())
        while self.current_token.type == NEWLINE:
            self.consume_token(NEWLINE)
            root.children.append(self.statement())

        return root

    def statement(self):
        if self.current_token.type == IF:
            node = self.if_statement()

        elif (self.current_token.type == IDENTIFIER
              and self.lookahead(1).type == ASSIGN):
            node = self.assign_statement()

        elif self.current_token.type in builtin_functions:
            node = self.builtin_function()

        elif self.current_token.type in object_types:
            node = self.expression()

        elif self.current_token.type in (LPAREN, ADD, SUB):
            node = self.expression()

        else:
            node = self.empty()

        return node

    def assign_statement(self):
        left = self.variable()

        token = self.current_token
        self.consume_token(ASSIGN)

        return Assign(left_node=left,
                      operator=token,
                      right_node=self.expression())

    def builtin_function(self):
        token = self.current_token
        function = builtin_functions[token.type]

        self.consume_token(function.name)
        self.consume_token(LBRACKET)

        if function.arbitrary:
            args = self.arbitrary_argument_list()

        else:
            args = []
            for i, arg_name in enumerate(function.arg_names):
                try:
                    args.append(self.expression())
                    if i < len(function.arg_names) - 1:
                        self.consume_token(COMMA)
                except SyntaxError as e:
                    raise SyntaxError('Invalid syntax: expected argument {}: {}'
                                      .format(i + 1, arg_name))

        self.consume_token(RBRACKET)

        modifiers = self.modifiers_flags_list()  # dict with 1 nested list
        flags = modifiers['flags']
        del modifiers['flags']

        for flag in flags:
            if flag not in function.flags:
                raise SyntaxError('Invalid syntax: unexpected flag {}'
                                  .format(flag))

        for mod_name in modifiers.keys():
            if mod_name not in function.modifiers:
                raise SyntaxError('Invalid syntax: unexpected modifier {} ({})'
                                  .format(mod_name, modifiers[mod_name]))

        return FunctionCall(function  = function,
                            args      = args,
                            modifiers = modifiers,
                            flags     = flags)

    def arbitrary_argument_list(self):
        try:
            results = [self.expression()]
        except SyntaxError:  # no expression found, got [
            results = []
            return results
        while self.current_token.type == COMMA:
            self.consume_token(COMMA)
            results.append(self.expression())

        return results

    def modifiers_flags_list(self):
        results = {'flags': []}
        while self.current_token.type == TILDE:
            self.consume_token(TILDE)
            if self.current_token.value in flag_names:
                results['flags'].append(self.current_token.value)
                self.consume_token(IDENTIFIER)

            else:
                modifier = self.assign_statement()

                name = modifier.left.value    # Variable.value
                value = modifier.right.value  # expression()
                results[name] = value

        return results

    def empty(self):
        return Empty()

    def variable(self):
        node = Variable(self.current_token)

        if not self.current_token.value in self.seen_variables:
            self.seen_variables.append(self.current_token.value)

        self.consume_token(IDENTIFIER)
        return node

    def if_statement(self):
        token = self.current_token
        elif_expressions = []
        elif_blocks = []
        else_block = None
        self.consume_token(IF)
        self.consume_token(LBRACKET)

        expression = self.expression()

        self.consume_token(RBRACKET)
        self.consume_token(COMMA)
        self.consume_token(THEN)
        self.consume_token(NEWLINE)

        block = self.indented_statement_list()

        # print('\n'.join(str(n) for n in block.children))
        # print(self.current_token.type)
        # print()
        if self.current_token.type == ENDIF:
            self.consume_token(ENDIF)

        else:
            while self.current_token.type != ENDIF:
            # check for else, if clauses
                if self.current_token.type == ELSE:
                # and else clause (if any)
                    self.consume_token(ELSE)

                    if self.current_token.type == COMMA:
                    # continue into else, if
                        self.consume_token(COMMA)
                        self.consume_token(IF)
                        self.consume_token(LBRACKET)

                        elif_expressions.append(self.expression())

                        self.consume_token(RBRACKET)
                        self.consume_token(COMMA)
                        self.consume_token(THEN)
                        self.consume_token(NEWLINE)

                        elif_blocks.append(self.indented_statement_list())

                    else:  # continue into else clause
                        self.consume_token(NEWLINE)
                        else_block = self.indented_statement_list()
                        self.consume_token(ENDIF)
                        # expect end after else clause
                        break

                else:
                    self.raise_error(self.current_token)

        return IfStatement(token       = token,
                           expression  = expression,
                           block       = block,
                           elif_expressions = elif_expressions,
                           elif_blocks = elif_blocks,
                           else_block  = else_block)

    def indented_statement_list(self):
        self.indentation_level += 1

        # print('indented:', self.indentation_level, end='')
        node = StatementList()
        self.consume_pipe()
        node.children.append(self.statement())
        self.consume_token(NEWLINE)

        while (self.current_token.type == PIPE
               and len(self.current_token.value) == self.indentation_level):
            self.consume_pipe()

            node.children.append(self.statement())
            self.consume_token(NEWLINE)

        self.indentation_level -= 1
        if self.indentation_level > 0:
            self.consume_pipe()

        return node

    def consume_pipe(self):
        if self.current_token.type == PIPE:
            if len(self.current_token.value) == self.indentation_level:
                self.consume_token(PIPE)
            else:
                self.raise_error(token_type='|' * self.indentation_level,
                                 received  =self.current_token.value)
        else:
            self.raise_error(token_type='|' * self.indentation_level,
                             received  =self.current_token.value)


    def expression(self):
        return self.comparison()

    def comparison(self):
        node = self.addition()
        while self.current_token.type in (EQUAL, N_EQUAL, L_EQUAL,
                                          G_EQUAL, LESS, GREATER):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.addition())
        return node

    def addition(self):
        node = self.multiplication()
        while self.current_token.type in (ADD, SUB):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.multiplication())
        return node

    def multiplication(self):
        node = self.unary()
        while self.current_token.type in (MUL, DIV, FLOORDIV):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.unary())

        return node

    def unary(self):
        token = self.current_token
        if token.type in (ADD, SUB):
            self.consume_token(token.type)
            return UnaryOperation(operator   = token,
                                  expression = self.unary())

        elif token.type == LPAREN:
            return self.exponent()

        elif token.type in builtin_functions:
            return self.exponent()

        elif token.type in object_types:
            return self.exponent()

        else:
            self.raise_error(token)

    def exponent(self):
        node = self.atom()
        while self.current_token.type == POWER:
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.exponent())

        return node

    def atom(self):
        token = self.current_token
        if token.type == NUM:
            self.consume_token(NUM)
            return Number(token)

        elif token.type == STR:
            self.consume_token(STR)
            return String(token)

        elif token.type == LPAREN:
            return self.paren_expr()

        elif token.type == IDENTIFIER:
            return self.variable()

        elif token.type in builtin_functions:

            return self.builtin_function()

        elif token.type in (TRUE, FALSE):
            self.consume_token(token.type)
            return Boolean(token)

        if token.type in (ADD, SUB):
            self.consume_token(token.type)
            return UnaryOperation(operator   = token,
                                  expression = self.atom())

        else:
            self.raise_error(token)

    def paren_expr(self):
        self.consume_token(LPAREN)
        node = self.expression()
        self.consume_token(RPAREN)
        return node

    def parse(self):
        node = self.program()
        if self.current_token.type not in (EOF, NEWLINE):
            self.raise_error(self.current_token)

        return node
