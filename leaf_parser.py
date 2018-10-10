"""Parser for Leaf."""

from leaf_tokens import *
from leaf_ast import *
from leaf_types_interpreter import *


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.indentation_level = 0
        self.buffer = []
        self.previous = None
        self.current_token = self.next_token()

    def lookahead(self, n=1):
        while len(self.buffer) < n:
            self.buffer.append(self.next_token())
        return self.buffer[n - 1]

    def next_token(self):
        if self.buffer:
            token = self.buffer.pop(0)
        else:
            token = self.lexer.next_token()

        return token

    def consume_token(self, token_type):
        if self.current_token.type == token_type:
            self.previous = self.current_token
            self.current_token = self.next_token()
        else:
            self.raise_error(token_type=token_type,
                             received=self.current_token.type)
        # print(self.current_token, end='')
        # print(self.current_token.type)

    def consume_identifier(self):
        # for name in identifier_subtypes:
        for name in identifier_subtypes:
            try:
                self.consume_token(name)
            except SyntaxError:
                continue
            else:
                return
        raise SyntaxError('name {} ({}) is not an identifier'
                          .format(self.current_token.value,
                                  self.current_token.type))

    def consume_optional_newline(self):
        if self.current_token.type == NEWLINE:
            self.consume_token(NEWLINE)

    def raise_error(self, token=None, *, token_type=None, received=None):
        # print('CURRENT TOKEN:', self.current_token)
        # print('indentation_level', self.indentation_level)
        if token:
            raise SyntaxError('Invalid syntax in line {}:\nin: {}\n{} ({})'
                              .format(token.line,
                                      token.lookahead,
                                      str(token.value),
                                      token.type))
        elif token_type and received:
            raise SyntaxError('Invalid syntax in line {}:\nin: {}\nexpected {}, got {}'
                              .format(self.current_token.line,
                                      self.current_token.lookahead,
                                      token_type,
                                      received))
        else:
            raise SyntaxError('Invalid syntax')

    def program(self):
        return self.statement_list()

    def statement_list(self):
        root = StatementList()
        root.children.append(self.statement())
        while self.current_token.type == NEWLINE:
            self.consume_token(NEWLINE)
            statement = self.statement()
            if statement is None:
                continue
            root.children.append(statement)

        return root

    def statement(self):
        token = self.current_token
        if token.type == IF:
            node = self.if_statement()

        elif token.type == WHILE:
            node = self.while_loop()

        elif token.type == UNTIL:
            node = self.until_loop()

        elif token.type == FOR:
            node = self.for_loop()

        elif token.type == FUNC:
            node = self.function_definition()

        elif (token.type in identifier_subtypes
              and self.lookahead(1).type == ASSIGN):
            node = self.assign_statement()

        elif (token.type == IDENTIFIER
              and self.lookahead(1).type == COMMA):
            node = self.multiple_assign_statement()

        elif (token.type in identifier_subtypes
              and self.lookahead(1).type == DOT):
            node = self.possible_assign()

        elif token.type in object_types:
            node = self.expression()

        elif token.type in expression_starters:
            node = self.expression()

        elif token.type == RETURN:
            node = self.return_statement()

        elif token.type in (NEXT, BREAK):
            node = LoopControl(self.current_token)
            self.consume_token(token.type)

        else:
            # node = self.empty()
            node = None

        return node

    def assign_statement(self):
        left = self.identifier()

        token = self.current_token
        self.consume_token(ASSIGN)

        right = self.expression()

        node = Assign(left_node  = left,
                      operator   = token,
                      right_node = right)
        return node

    def possible_assign(self):
        node = self.identifier()
        while self.current_token.type == DOT:
            self.consume_token(DOT)
            attr = self.current_token
            self.consume_identifier()
            node = AttributeAccess(node, attr)

        if self.current_token.type == ASSIGN:
            token = self.current_token
            self.consume_token(ASSIGN)

            right = self.expression()

            node = Assign(left_node  = node,
                          operator   = token,
                          right_node = right)

        elif self.current_token.type == LBRACKET:
            args, modifiers, flags = self.function_call()
            node = FunctionCall(function_node = node,
                                args          = args,
                                modifiers     = modifiers,
                                flags         = flags)

        return node


    def multiple_assign_statement(self):
        token = self.current_token

        if self.current_token.type == COLON:
            token = self.current_token
            self.consume_token(COLON)
            variables = [IterableUnpacking(token, self.identifier())]

        else:
            variables = [self.identifier()]
        # require at least one variable to assign to

        if self.current_token.type == COMMA:
            self.consume_token(COMMA)
            if self.current_token.type not in (COLON, IDENTIFIER):
                self.raise_error(token)
            variables.extend(self.arbitrary_unpacking_identifier_list())

        self.consume_token(ASSIGN)

        args = [self.expression()]
        if self.current_token.type == COMMA:
            self.consume_token(COMMA)
            args.extend(self.arbitrary_argument_list())

        node = MultipleAssign(token, variables, args)

        return node

    def function_call(self):

        self.consume_token(LBRACKET)
        self.consume_optional_newline()

        args = self.arbitrary_argument_list()
        modifiers, flags = self.modifiers_flags_list()
        # 2 dicts

        self.consume_token(RBRACKET)

        return args, modifiers, flags

    def function_definition(self):
        self.consume_token(FUNC)
        self.consume_token(LBRACKET)

        token = self.current_token
        self.consume_identifier()

        self.consume_token(RBRACKET)
        self.consume_token(ASSIGN)
        self.consume_token(LBRACKET)

        args, arbitrary, modifiers, flags = self.function_parameters()

        self.consume_token(RBRACKET)
        self.consume_token(COMMA)
        self.consume_token(DO)
        self.consume_token(NEWLINE)

        body = self.indented_statement_list()

        self.consume_token(ENDFUNC)

        return FunctionDefinition(token     = token,
                                  arg_names = args,
                                  arbitrary = arbitrary,
                                  modifiers = modifiers,
                                  flags     = flags,
                                  body      = body)

    def return_statement(self):
        token = self.current_token
        self.consume_token(RETURN)
        if self.current_token.type in (NEWLINE, EOF):
            # the statementlist parser consumes newlines
            node = Return(token, None)

        else:
            self.consume_token(LBRACKET)
            node = Return(token, self.expression())
            self.consume_token(RBRACKET)

        return node

    def function_parameters(self):
        args = []
        arbitrary = None
        flags = []
        modifiers = {}
        while self.current_token.type == IDENTIFIER:
            args.append(self.identifier())
            if self.current_token.type == COMMA:
                self.consume_token(COMMA)
            else:
                break

        if self.current_token.type == COLON:
            self.consume_token(COLON)
            arbitrary = self.current_token.value
            self.consume_identifier()

        while self.current_token.type == TILDE:
            self.consume_token(TILDE)
            if (self.current_token.type == IDENTIFIER
                and self.lookahead(1).type == ASSIGN):
                modifier = self.assign_statement()

                name = modifier.left.value    # Variable
                value = modifier.right        # expression()
                modifiers[name] = value

            else:
                flags.append(self.current_token.value)
                self.consume_identifier()

            self.consume_optional_newline()

        return args, arbitrary, modifiers, flags

    def arbitrary_argument_list(self):
        if (self.current_token.type in object_types
            or self.current_token.type in expression_starters):

            results = [self.expression()]
            self.consume_optional_newline()

        else:
            return []

        while self.current_token.type == COMMA:
            self.consume_token(COMMA)

            results.append(self.expression())

            self.consume_optional_newline()

        return results

    def modifiers_flags_list(self):
        modifiers = {}
        flags = {}
        while self.current_token.type == TILDE:
            self.consume_token(TILDE)
            if (self.current_token.type == IDENTIFIER
                and self.lookahead(1).type == ASSIGN):
                modifier = self.assign_statement()

                name = modifier.left.value    # Variable
                value = modifier.right        # expression()
                modifiers[name] = value

            else:
                flags[self.current_token.value] = true
                self.consume_identifier()

            self.consume_optional_newline()

        return (modifiers, flags)

    def empty(self):
        return Empty()

    def identifier(self):
        node = Variable(self.current_token)

        self.consume_identifier()
        return node

    def if_statement(self):
        token = self.current_token
        # used to create the ifstatement object
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
            else:
                self.consume_token(ENDIF)
                # consume if unbroken (on an else,if without an else)

        node = IfStatement(token       = token,
                           expression  = expression,
                           block       = block,
                           elif_expressions = elif_expressions,
                           elif_blocks = elif_blocks,
                           else_block  = else_block)
        return node

    def while_loop(self):
        token = self.current_token
        # used to create the whileloop object
        self.consume_token(WHILE)
        self.consume_token(LBRACKET)

        expression = self.expression()

        self.consume_token(RBRACKET)
        self.consume_token(COMMA)
        self.consume_token(LOOP)
        self.consume_token(NEWLINE)

        block = self.indented_statement_list()

        self.consume_token(ENDLOOP)

        node = WhileLoop(token      = token,
                         expression = expression,
                         block      = block)
        return node

    def until_loop(self):
        token = self.current_token
        # used to create the whileloop object
        self.consume_token(UNTIL)
        self.consume_token(LBRACKET)

        expression = self.expression()

        self.consume_token(RBRACKET)
        self.consume_token(COMMA)
        self.consume_token(LOOP)
        self.consume_token(NEWLINE)

        block = self.indented_statement_list()

        self.consume_token(ENDLOOP)

        node = UntilLoop(token      = token,
                         expression = expression,
                         block      = block)
        return node

    def for_loop(self):
        token = self.current_token
        # used to create for loop object
        self.consume_token(FOR)
        self.consume_token(LBRACKET)

        params = self.arbitrary_identifier_list()

        self.consume_token(RBRACKET)
        self.consume_token(IN)
        self.consume_token(LBRACKET)

        if self.current_token.type == COLON:
            self.consume_token(COLON)
            iterable = IterableUnpacking(self.current_token,
                                         self.expression())
        else:
            iterable = self.expression()

        self.consume_token(RBRACKET)
        self.consume_token(COMMA)
        self.consume_token(LOOP)
        self.consume_token(NEWLINE)

        block = self.indented_statement_list()

        self.consume_token(ENDLOOP)

        return ForLoop(token      = token,
                       parameters = params,
                       iterable   = iterable,
                       block      = block)

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

    def arbitrary_unpacking_identifier_list(self):
        results = []
        if self.current_token.type == IDENTIFIER:
            results.append(self.identifier())

        elif self.current_token.type == COLON:
            token = self.current_token
            self.consume_token(COLON)
            results.append(IterableUnpacking(token, self.identifier()))

        else:
            return results

        while self.current_token.type == COMMA:
            self.consume_token(COMMA)

            if self.current_token.type == COLON:
                token = self.current_token
                self.consume_token(COLON)
                results.append(IterableUnpacking(token, self.identifier()))

            else:
                results.append(self.identifier())

            self.consume_optional_newline()

        return results

    def arbitrary_identifier_list(self):
        results = []
        if self.current_token.type == IDENTIFIER:
            results.append(self.identifier())

        else:
            return results

        while self.current_token.type == COMMA:
            self.consume_token(COMMA)

            results.append(self.identifier())

            self.consume_optional_newline()

        return results

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
        if self.current_token.type == COLON:
            self.consume_token(COLON)
            return IterableUnpacking(self.current_token,
                                     self.comparison())
        else:
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
        while self.current_token.type in (MUL, DIV, FLOORDIV, MOD):
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
            node = UnaryOperation(operator   = token,
                                  expression = self.unary())

        elif token.type in (LPAREN, LBRACKET, COLON):
            node = self.exponent()

        elif token.type in object_types:
            node = self.exponent()

        else:
            self.raise_error(token)

        return node

    def exponent(self):
        node = self.object_manipulation()
        while self.current_token.type == POWER:
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.exponent())
        return node

    def object_manipulation(self):
        node = self.atom()
        while self.current_token.type in (LBRACKET, DOT):
            token = self.current_token
            if token.type == DOT:
                self.consume_token(DOT)
                attr = self.current_token
                self.consume_identifier()
                node = AttributeAccess(node, attr)

            elif token.type == LBRACKET:
                args, modifiers, flags = self.function_call()
                node = FunctionCall(function_node = node,
                                    args          = args,
                                    modifiers     = modifiers,
                                    flags         = flags)

        return node

    def atom(self):
        token = self.current_token
        # print(repr(self.current_token))

        if token.type in object_types:
            if token.type == NUM:
                self.consume_token(NUM)
                node = Number(token)

            elif token.type == STR:
                self.consume_token(STR)
                node = String(token)

            elif token.type == TRUE:
                self.consume_token(TRUE)
                node = true

            elif token.type == FALSE:
                self.consume_token(FALSE)
                node = false

            elif token.type == NONE:
                self.consume_token(NONE)
                node = none

            elif token.type in identifier_subtypes:  # this excludes literals
                node = self.identifier()

            else:
                self.raise_error(token)

        elif token.type == LBRACKET:   # List
            node = self.enclosure()

        elif token.type == LPAREN:
            node = self.paren_expr()

        elif token.type == COLON:
            self.consume_token(COLON)
            node = IterableUnpacking(token,
                                     self.atom())

        elif token.type in (ADD, SUB):
            self.consume_token(token.type)
            node = UnaryOperation(operator   = token,
                                  expression = self.atom())

        else:
            self.raise_error(token)

        return node

    def paren_expr(self):
        self.consume_token(LPAREN)
        node = self.expression()
        self.consume_token(RPAREN)
        return node

    def enclosure(self):
        self.consume_token(LBRACKET)

        objects = self.arbitrary_argument_list()
        node = List(Token(LIST, objects))

        self.consume_token(RBRACKET)

        return node

    def parse(self):
        node = self.program()
        if self.current_token.type not in (EOF, NEWLINE):
            self.raise_error(self.current_token)

        return node

