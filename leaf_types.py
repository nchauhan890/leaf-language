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

    'LBRACKET',
    'RBRACKET',

    'LPAREN',
    'RPAREN',

    'IDENTIFIER',

    'SHOW',
    'JOIN',
    'STR_FUNC',
    'NUM_FUNC',

    'IF',
    'THEN',
    'ELSE',
    'ENDIF',

    'reserved_keywords',
    'builtin_functions',
    'flag_names',
    'object_types',

    'true',
    'false',

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
                 modifiers=None,
                 flags=None):  # dict
        self.token = token
        self.name = token.type
        if not arbitrary:
            self.arbitrary = False
            self.arg_names = (arg_names
                              if arg_names is not None
                              else [])
        else:
            self.arbitrary = True

        self.modifiers = modifiers if modifiers is not None else []
        self.flags = flags if flags is not None else []


class Type:
    def __init__(self, token, *,
                error_msg='{}',
                expected_type=None,
                expected_value=None):
        self.token = token
        self.value = token.value
        if '{}' not in error_msg:
            raise TypeError()
        if expected_type:
            if not isinstance(self.value, expected_type):
                raise TypeError(error_msg.format(self.value.__class__.__name__))
        if isinstance(expected_value, (tuple, list)):
            if self.value not in expected_value:
                raise TypeError(error_msg.format(self.value.__class__.__name__))

        elif expected_value:
            if self.value != expected_value:
                raise TypeError(error_msg.format(self.value.__class__.__name__))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.token))

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

    def __init_subclass__(cls):
        super(Type, cls).__init_subclass__()

    # binary operation methods (arithmetic)

    def __add__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(self.token.type, val_1 + val_2))

        elif (isinstance(other, String)
            and isinstance(self, String)):
            val_1 = str(self)
            val_2 = str(other)
            return String(Token(self.token.type, val_1 + val_2))

        else:
            self.unsupported_binary_op('+', self, other)

    def __sub__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(self.token.type, val_1 - val_2))

        else:
            self.unsupported_binary_op('-', self, other)

    def __mul__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(self.token.type, val_1 * val_2))

        elif (isinstance(other, String)
              and isinstance(self, Number)):
            if not self.is_integer():
                raise TypeError('cannot multiply String by non-integer Number')
            val_1 = int(self.value)
            val_2 = other.value
            return String(Token(self.token.type, val_1 * val_2))

        elif (isinstance(other, Number)
              and isinstance(self, String)):
            if not other.is_integer():
                raise TypeError('cannot multiply String by non-integer Number')
            val_1 = self.value
            val_2 = int(other.value)
            return String(Token(self.token.type, val_1 * val_2))

        else:
            self.unsupported_binary_op('*', self, other)

    def __truediv__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if float(val_2) == 0.0:
                raise ZeroDivisionError('attempted division by zero')
            return Number(Token(self.token.type, val_1 / val_2))

        else:
            self.unsupported_binary_op('/', self, other)

    def __floordiv__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if float(val_2) == 0.0:
                raise ZeroDivisionError('attempted floor division by zero')
            return Number(Token(self.token.type, val_1 // val_2))

        else:
            self.unsupported_binary_op('//', self, other)

    def __pow__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(self.token.type, val_1 ** val_2))

        else:
            self.unsupported_binary_op('^', self, other)

    # Comparison methods

    def __eq__(self, other):
        if (isinstance(other, (String, Number))
            and isinstance(self, (String, Number))):
            val_1 = self.value
            val_2 = other.value
            if val_1 == val_2:
                # return Boolean(Token(TRUE, 'true'))
                return true
            else:
                # return Boolean(Token(FALSE, 'false'))
                return false

        else:
            self.unsupported_binary_op('=', self, other)

    def __ne__(self, other):
        if (isinstance(other, (String, Number))
            and isinstance(self, (String, Number))):
            val_1 = self.value
            val_2 = other.value
            if val_1 != val_2:
                return true
            else:
                return false

        else:
            self.unsupported_binary_op('!', self, other)

    def __lt__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if val_1 < val_2:
                return true
            else:
                return false

        else:
            self.unsupported_binary_op('<', self, other)

    def __gt__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if val_1 > val_2:
                return true
            else:
                return false

        else:
            self.unsupported_binary_op('>', self, other)

    def __le__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if val_1 <= val_2:
                return true
            else:
                return false

        else:
            self.unsupported_binary_op('<=', self, other)

    def __ge__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if val_1 >= val_2:
                return true
            else:
                return false

        else:
            self.unsupported_binary_op('>=', self, other)

    # Unary operation methods

    def __neg__(self):
        if isinstance(self, Number):
            return Number(Token(self.token.type, -self.value))

        else:
            self.unsupported_unary_op('+', self)

    def __pos__(self):
        if isinstance(self, Number):
            return Number(Token(self.token.type, +self.value))

        else:
            self.unsupported_unary_op('+', self)

    # __radd__ = __add__
    # __rsub__ = __sub__
    # __rmul__ = __mul__
    # __rtruediv__ = __truediv__
    # __rfloordiv__ = __floordiv__
    # __rpow__ = __pow__

    def __bool__(self):
        return bool(self.value)


class Number(Type):
    def __init__(self, token):
        msg = 'expected python <decimal.Decimal> type, got <{}>'
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=decimal.Decimal)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def is_integer(self):
        return int(self) == float(self)


class String(Type):
     def __init__(self, token):
        msg = 'expected python <str> type, got <{}>'
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=str)


class Boolean(Number):
    def __init__(self, token):
        msg = 'expected python <str: \'true\' or \'false\'> type, got <{}>'
        if token.type == TRUE:
            token = Token(NUM, decimal.Decimal(1))
        elif token.type == FALSE:
            token = Token(NUM, decimal.Decimal(0))
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=decimal.Decimal)

    # def __int__(self):
    #     return 1 if self.value == 'true' else 0

    # def __float__(self):
    #     return float(int(self))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.token))

    def __str__(self):
        return 'false' if int(self.value) == 0 else 'true'


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

LBRACKET = 'LBRACKET'  # [
RBRACKET = 'RBRACKET'  # ]

LPAREN = 'LPAREN'  # (
RPAREN = 'RPAREN'  # )

IDENTIFIER = 'IDENTIFIER'

SHOW = 'SHOW'   # print function
JOIN = 'JOIN'   # join function
STR_FUNC = 'STR_FUNC'  # str[] functions
NUM_FUNC = 'NUM_FUNC'  # int[]

IF = 'IF'       # if statements:
THEN = 'THEN'
ELSE = 'ELSE'
ENDIF = 'ENDIF'

reserved_keywords = {
    'str': Token(STR_FUNC, 'str'),
    'num': Token(NUM_FUNC, 'num'),
    'show': Token(SHOW, 'show'),
    'join': Token(JOIN, 'join'),

    'if': Token(IF, 'if'),
    'then': Token(THEN, 'then'),
    'else': Token(ELSE, 'else'),
    'endif': Token(ENDIF, 'endif'),

    'true': Token(TRUE, 'true'),
    'false': Token(FALSE, 'false')
    }

builtin_functions = {
    SHOW: Function(token     = Token(SHOW, 'show'),
                   arg_names = None,
                   arbitrary = True,
                   modifiers = ['end', 'sep'],
                   flags     = ['comma_sep', 'no_newline']),

    JOIN: Function(token     = Token(JOIN, 'join'),
                   arg_names = None,
                   arbitrary = True,
                   modifiers = ['end', 'sep', 'start'],
                   flags     = ['comma_sep']),

    STR_FUNC: Function(token     = Token(STR_FUNC, 'str'),
                       arg_names = ['value'],
                       arbitrary = False),

    NUM_FUNC: Function(token     = Token(NUM_FUNC, 'num'),
                       arg_names = ['value'],
                       arbitrary = False),
    }

flag_names = [
    'comma_sep',
    'no_newline',
    ]

object_types = [
    STR,
    NUM,

    TRUE,
    FALSE,

    IDENTIFIER
    ]

true = Boolean(Token(TRUE, 'true'))
false = Boolean(Token(FALSE, 'false'))

whitespace = string.whitespace
digits = string.digits
letters = string.ascii_letters
letters_under = string.ascii_letters + '_'
letters_identifier = digits + letters_under
string_characters = (letters + digits + whitespace
                     + r'`!"£$%^&*()_-+={[}]:;@~#<,>.?\/€')
