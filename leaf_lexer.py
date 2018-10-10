"""Lexer for Leaf."""

import decimal

from leaf_tokens import *

class Lexer:

    def __init__(self, source):
        self.source = source + '\n'
        self.pos = 0
        self.current_char = self.source[self.pos]
        self.previous_text = ''
        self.line = 1

    def raise_error(self, received_val=None):
        if received_val is not None:
            raise TypeError("Invalid character '{}'\nin line {}"
                            .format(received_val, self.line))
        else:
            raise TypeError('Invalid character in line {}'
                            .format(self.line))

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

        token = reserved_keywords.get(result,
                                      Token(IDENTIFIER, result))
        # previous text includes the identifier name
        return token

    def collect_string(self):
        result = ''
        self.advance()    # skip quote '
        while (self.current_char is not None
               and self.current_char in string_characters):
            if (self.current_char == '\\'
                and self.peek(1) == '\\'):
                result += '\\'
                self.advance()

            elif (self.current_char == '\\'
                  and self.peek(1) == 'n'):
                result += '\n'
                self.advance()

            else:
                result += self.current_char
            self.advance()

        if not self.current_char == '\'':
            self.raise_error(repr(self.current_char))
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
        if self.current_char in ('\n', ';'):
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
        if self.current_char == '\n':
            self.line += 1
        self.previous_text = (self.previous_text + self.current_char)[-20:]
        # preserves length of 10 for previous text

        if self.pos >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.pos]

    def next_token(self):
        while self.current_char is not None:
            if self.current_char in ('\n', ';'):  # check newlines first
                token = self.newline()             # semicolon ; counts
                                                  # as newline too
            elif self.current_char in whitespace:
                token = self.skip_whitespace()

            elif self.current_char == '#':
                token = self.comment()

            elif self.current_char in digits:
                token = Token(NUM, self.collect_number())

            elif self.current_char in letters_under:  # can't start
                token = self.identifier()              # with number

            elif self.current_char == '\'':       # strings start with '
                token = Token(STR, self.collect_string())



            elif (self.current_char == '<'   # check assign <<
                  and self.peek(1) == '<'):  # before less than <
                self.advance()
                self.advance()
                token = Token(ASSIGN, '<<')

            elif (self.current_char == '>'
                  and self.peek(1) == '>'):   # check >> (range)
                self.advance()                # before > (greater than)
                self.advance()
                token = Token(RANGE, '>>')

            elif self.current_char == '|':
                token = self.indent()

            elif self.current_char == ',':
                self.advance()
                token = Token(COMMA, ',')

            elif self.current_char == '~':
                self.advance()
                token = Token(TILDE, '~')

            elif self.current_char == '.':
                self.advance()
                token = Token(DOT, '.')

            elif self.current_char == ':':
                self.advance()
                token = Token(COLON, ':')



            elif self.current_char == '=':
                self.advance()
                token = Token(EQUAL, '=')

            elif self.current_char == '!':
                self.advance()
                token = Token(N_EQUAL, '!')

            elif (self.current_char == '>'     # check the double
                  and self.peek(1) == '='):    # character >= and <=
                self.advance()                 # before < and >
                self.advance()
                token = Token(G_EQUAL, '>=')

            elif (self.current_char == '<'
                  and self.peek(1) == '='):
                self.advance()
                self.advance()
                token = Token(L_EQUAL, '<=')

            elif self.current_char == '>':
                self.advance()
                token = Token(GREATER, '>')

            elif self.current_char == '<':
                self.advance()
                token = Token(LESS, '<')



            elif (self.current_char == '*'
                  and self.peek(1) == '*'):
                self.advance()
                self.advance()
                token = Token(POWER, '**')

            elif self.current_char == '+':
                self.advance()
                token = Token(ADD, '+')

            elif self.current_char == '-':
                self.advance()
                token = Token(SUB, '-')

            elif (self.current_char == '/'
                  and self.peek(1) == '/'):    # floor div
                self.advance()
                self.advance()                 # check floor div //
                token = Token(FLOORDIV, '//')  # before normal /

            elif self.current_char == '/':
                self.advance()
                token = Token(DIV, '/')
                # normal div

            elif self.current_char == '*':
                self.advance()
                token = Token(MUL, '*')

            elif self.current_char == '%':
                self.advance()
                token = Token(MOD, '%')



            elif self.current_char == '(':
                self.advance()
                token = Token(LPAREN, '(')

            elif self.current_char == ')':
                self.advance()
                token = Token(RPAREN, ')')

            elif self.current_char == '[':
                self.advance()
                token = Token(LBRACKET, '[')

            elif self.current_char == ']':
                self.advance()
                token = Token(RBRACKET, ']')


            else:
                self.raise_error(self.current_char)

            if token is not None:
                token.lookahead = (self.previous_text.split('\n')[-1]
                                   + (self.current_char
                                     if self.current_char is not None
                                     else '')
                                   + self.peek(10).split('\n')[0])
                token.line = self.line

                return token

        token = Token(EOF, '')
        return token
