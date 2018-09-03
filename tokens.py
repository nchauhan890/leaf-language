"""Token class with token types."""

import string
import decimal

__all__ = [
    'Token',
    'Type',
    'Function',
    'Boolean',
    'String',
    'Number',

    'EOF',
    'NEWLINE',

    'PIPE',
    'COMMA',
    'ASSIGN',
    'TILDE',

    'NUM',
    'STR',

    'TRUE',
    'FALSE',

    'ADD',
    'SUB',
    'MUL',
    'DIV',
    'FLOORDIV',
    'POWER',

    'EQUAL',
    'N_EQUAL',
    'G_EQUAL',
    'L_EQUAL',
    'GREATER',
    'LESS',

    'STR_TYPE',
    'NUM_TYPE',

    'LBRACKET',
    'RBRACKET',

    'LPAREN',
    'RPAREN',

    'IDENTIFIER',

    'SHOW',

    'reserved_keywords',
    'builtin_functions',

    'whitespace',         # includes newline
    'digits',             # == regex [0-9]
    'letters',            # == regex [a-zA-Z]
    'letters_under',      # == regex [a-zA-Z_]
    'letters_identifier', # == regex [a-zA-Z0-9_]
    'string_characters'
    ]
    


class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value
        # print(self.type)

    def __repr__(self):
        return 'Token({}, {})'.format(self.type,
                                      repr(self.value))

    def __str__(self):
        return str(self.value)


class Function:
    def __init__(self, *,
                 token,            # token
                 arg_names=None,   # list
                 arbitrary=False,  # True/False
                 modifiers=None):  # dict
        self.token = token
        self.name = token.type
        if arbitrary is not True:
            self.arbitrary = False
            self.arg_names = (arg_names
                              if arg_names is not None
                              else [])
        else:
            self.arbitrary = True
            
        self.modifiers = (modifiers
                               if modifiers is not None
                               else [])


class Type:
    def __init__(self, token, *, error_msg='{}', expected_type=None):
        self.token = token
        self.value = token.value
        if '{}' not in error_msg:
            raise TypeError()
        if expected_type:
            if not isinstance(self.value, expected_type):
                raise TypeError(error_msg.format(self.value.__class__.__name__))

    def __repr__(self):
        return 'Number({})'.format(repr(self.token))

    def __str__(self):
        return str(self.value)

    def unsupported_binary_op(self, op, obj1, obj2):
        raise TypeError('Invalid operation: {} {} {}'
                        .format(obj1.__class__.__name__,
                                op,
                                obj2.__class__.__name__))

    def unsupported_unary_op(self, op, obj):
        raise TypeError('Invalid operation: {} {}'
                        .format(op, obj.__class__.__name__))

    ### default operations

    def supports_binary_operations(self):

        def __add__(self, other):
            if isinstance(other, self.__class__):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 + num2))

            else:
                self.unsupported_binary_op('+', self, other)

        def __sub__(self, other):
            if isinstance(other, Number):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 - num2))

            else:
                self.unsupported_binary_op('-', self, other)

        def __mul__(self, other):
            if isinstance(other, Number):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 * num2))

            else:
                self.unsupported_binary_op('*', self, other)

        def __truediv__(self, other):
            if isinstance(other, Number):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 / num2))

            else:
                self.unsupported_binary_op('/', self, other)

        def __floordiv__(self, other):
            if isinstance(other, Number):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 // num2))

            else:
                self.unsupported_binary_op('//', self, other)

        def __pow__(self, other):
            if isinstance(other, Number):
                num1 = self.value
                num2 = other.value
                return self.__class__(Token(self.token.type, num1 ** num2))

            else:
                self.unsupported_binary_op('^', self, other)

        __radd__ = __add__
        __rsub__ = __sub__
        __rmul__ = __mul__
        __rtruediv__ = __truediv__
        __rfloordiv__ = __floordiv__
        __rpow__ = __pow__

        names = {
            '__add__': __add__,
            '__sub__': __sub__,
            '__mul__': __mul__,
            '__truediv__': __truediv__,
            '__floordiv__': __floordiv__,
            '__pow__': __pow__,
            '__radd__': __radd__,
            '__rsub__': __rsub__,
            '__rmul__': __rmul__,
            '__rtruediv__': __rtruediv__,
            '__rfloordiv__': __rfloordiv__,
            '__rpow__': __rpow__
            }

        for name, func in names.items():
            setattr(self, name, func)

    def __eq__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 == num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('=', self, other)

    def __ne__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 != num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('!', self, other)

    def __lt__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 < num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('<', self, other)

    def __gt__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 > num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('>', self, other)

    def __le__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 <= num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('<=', self, other)

    def __ge__(self, other):
        if isinstance(other, Number):
            num1 = self.value
            num2 = other.value
            if num1 >= num2:
                return Boolean(Token(TRUE, 'True'))
            else:
                return Boolean(Token(FALSE, 'False'))

        else:
            self.unsupported_binary_op('>=', self, other)

    def __neg__(self):
        return self.__class__(Token(self.token.type, -self.value))

    def __pos__(self):
        return self.__class__(Token(self.token.type, +self.value))


class Number(Type):
    def __init__(self, token):
        msg = 'expected python <decimal.Decimal> type, got <{}>'
        super(Number, self).__init__(token,
                                     error_msg=msg,
                                     expected_type=decimal.Decimal)
        self.supports_binary_operations()


class String:
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Boolean:
    def __init__(self, token):
        self.token = token
        self.value = token.value
        if self.value not in ('True', 'False'):
            raise TypeError('expected True or False value, '
                            'got {}'.format(repr(self.value)))


EOF = 'EOF'
NEWLINE = 'NEWLINE'  # (\n)

PIPE = 'PIPE'  # |
COMMA = 'COMMA' # ,
ASSIGN = 'ASSIGN'  # <<
TILDE = 'TILDE'  # ~

NUM = 'NUM'
STR = 'STR'

TRUE = 'TRUE'
FALSE = 'FALSE'

ADD = 'ADD'  # +
SUB = 'SUB'  # -
MUL = 'MUL'  # *
DIV = 'DIV'  # /
FLOORDIV = 'FLOORDIV'  # //
POWER = 'POWER'

EQUAL = 'EQUAL'       # =
G_EQUAL = 'G_EQUAL'   # >=
L_EQUAL = 'L_EQUAL'   # >=
GREATER = 'GREATER'   # >
LESS = 'LESS'         # <
N_EQUAL = 'N_EQUAL'   # !

STR_TYPE = 'STR_TYPE'  # str
NUM_TYPE = 'NUM_TYPE'  # int

LBRACKET = 'LBRACKET'  # [
RBRACKET = 'RBRACKET'  # ]

LPAREN = 'LPAREN'  # (
RPAREN = 'RPAREN'  # )

IDENTIFIER = 'IDENTIFIER'

SHOW = 'SHOW'   # print function

reserved_keywords = {
    'str': Token(STR_TYPE, 'str'),
    'num': Token(NUM_TYPE, 'int'),
    'show': Token(SHOW, 'show')
    }

builtin_functions = {
    SHOW: Function(token     = Token(SHOW, 'show'),
                   arg_names = None,
                   arbitrary = True,
                   modifiers = ['end'])
    }


whitespace = string.whitespace
digits = string.digits
letters = string.ascii_letters
letters_under = string.ascii_letters + '_'
letters_identifier = digits + letters_under
string_characters = letters + digits + r'`!"£$%^&*()_-+={[}]:;@~#<,>.?\/€'
