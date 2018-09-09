"""Lexer for Leaf."""

import decimal

from leaf_types import *


class Lexer:

    def __init__(self, source):
        self.source = source + '\n'
        self.pos = 0
        self.current_char = self.source[self.pos]

    def raise_error(self, received_val=None):
        if received_val is not None:
            raise TypeError("Invalid character '{}'".format(received_val))
        else:
            raise TypeError('Invalid character')

    def peek(self, amount=1):
        result = ''
        for i in range(1, amount + 1):
            try:
                result += self.source[self.pos + i]
            except IndexError:
                break
        return result

    def skip_whitespace(self):
        while (self.current_char is not None
               and self.current_char in whitespace):
            self.advance()

    def collect_number(self):
        result = ''
        while (self.current_char is not None
               and self.current_char in digits):
            result += self.current_char
            self.advance()

        if self.current_char == '.':     # check for decimal point ONCE
            result += self.current_char
            self.advance()

        while (self.current_char is not None
               and self.current_char in digits):
            result += self.current_char
            self.advance()

        return decimal.Decimal(result)

    def identifier(self):
        result = self.current_char
        self.advance()
        while (self.current_char is not None
               and self.current_char in letters_identifier):
            result += self.current_char
            self.advance()

        return reserved_keywords.get(result, Token(IDENTIFIER, result))

    def collect_string(self):
        result = ''
        self.advance()    # skip quote '
        while (self.current_char is not None
               and self.current_char in string_characters):
            if (self.current_char == '\\'
                and self.peek(1) == 'n'):
                result += '\n'
                self.advance()

            else:
                result += self.current_char
            self.advance()

        if not self.current_char == '\'':
            self.raise_error(self.current_char)
        self.advance()

        return result  # already a string

    def newline(self):
        while self.current_char in ('\n', ';'):
            self.advance()

        return Token(NEWLINE, '\n')

    def comment(self):
        while (self.current_char not in ('\n', ';')
               and self.current_char is not None):
            self.advance()

    def indent(self):
        result = ''
        while self.current_char == '|':
            result += '|'
            self.advance()
            self.skip_whitespace()

        return Token(PIPE, result)

    def advance(self):
        self.pos += 1
        if self.pos >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.pos]

    def next_token(self):
        while self.current_char is not None:
            if self.current_char in ('\n', ';'):  # check newlines first
                return self.newline()             # semicolon ; counts
                                                  # as newline too
            elif self.current_char in whitespace:
                self.skip_whitespace()

            elif self.current_char == '#':
                self.comment()

            elif self.current_char in digits:
                return Token(NUM, self.collect_number())

            elif self.current_char in letters_under:  # can't start
                return self.identifier()              # with number

            elif self.current_char == '\'':       # strings start with '
                return Token(STR, self.collect_string())



            elif (self.current_char == '<'   # check assign <<
                  and self.peek(1) == '<'):  # before less than <
                self.advance()
                self.advance()
                return Token(ASSIGN, '<<')

            elif self.current_char == '|':
                return self.indent()

            elif self.current_char == ',':
                self.advance()
                return Token(COMMA, ',')

            elif self.current_char == '~':
                self.advance()
                return Token(TILDE, '~')



            elif self.current_char == '=':
                self.advance()
                return Token(EQUAL, '=')

            elif self.current_char == '!':
                self.advance()
                return Token(N_EQUAL, '!')

            elif (self.current_char == '>'     # check the double
                  and self.peek(1) == '='):    # character >= and <=
                self.advance()                 # before < and >
                self.advance()
                return Token(G_EQUAL, '>=')

            elif (self.current_char == '<'
                  and self.peek(1) == '='):
                self.advance()
                self.advance()
                return Token(L_EQUAL, '<=')

            elif self.current_char == '>':
                self.advance()
                return Token(GREATER, '>')

            elif self.current_char == '<':
                self.advance()
                return Token(LESS, '<')



            elif (self.current_char == '*'
                  and self.peek(1) == '*'):
                self.advance()
                self.advance()
                return Token(POWER, '**')

            elif self.current_char == '+':
                self.advance()
                return Token(ADD, '+')

            elif self.current_char == '-':
                self.advance()
                return Token(SUB, '-')

            elif (self.current_char == '/'
                  and self.peek(1) == '/'):    # floor div
                self.advance()
                self.advance()               # check floor div //
                return Token(FLOORDIV, '//') # before normal /

            elif self.current_char == '/':
                self.advance()
                return Token(DIV, '/')         # normal div

            elif self.current_char == '*':
                self.advance()
                return Token(MUL, '*')



            elif self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')

            elif self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            elif self.current_char == '[':
                self.advance()
                return Token(LBRACKET, '[')

            elif self.current_char == ']':
                self.advance()
                return Token(RBRACKET, ']')


            else:
                self.raise_error(self.current_char)

        return Token(EOF, None)
