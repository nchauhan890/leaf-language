"""Token types and other things for lexical analysis in Leaf."""

import string

EOF = 'EOF'
NEWLINE = 'NEWLINE'  # (\n)

PIPE = 'PIPE'      # |
COMMA = 'COMMA'    # ,
ASSIGN = 'ASSIGN'  # <<
RANGE = 'RANGE'    # >>
TILDE = 'TILDE'    # ~
DOT = 'DOT'        # .
COLON = 'COLON'    #

NUM = 'NUM'
STR = 'STR'
LIST = 'LIST'  # not actually used in lexical analysis
NONE = 'NONE'

TRUE = 'TRUE'      # true
FALSE = 'FALSE'    # false

ADD = 'ADD'               # +
SUB = 'SUB'               # -
MUL = 'MUL'               # *
DIV = 'DIV'               # /
FLOORDIV = 'FLOORDIV'     # //
POWER = 'POWER'           # **
MOD = 'MOD'

EQUAL = 'EQUAL'       # =
G_EQUAL = 'G_EQUAL'   # >=
L_EQUAL = 'L_EQUAL'   # >=
GREATER = 'GREATER'   # >
LESS = 'LESS'         # <
N_EQUAL = 'N_EQUAL'   # !

LBRACKET = 'LBRACKET'  # [
RBRACKET = 'RBRACKET'  # ]

LPAREN = 'LPAREN'      # (
RPAREN = 'RPAREN'      # )

IDENTIFIER = 'IDENTIFIER'
# now includes builtin function names

STR_OBJ = 'STR_OBJ'
NUM_OBJ = 'NUM_OBJ'     # class references/constructors
LIST_OBJ = 'LIST_OBJ'
BOOL_OBJ = 'BOOL_OBJ'
INDEX_OBJ = 'INDEX_OBJ'

IF = 'IF'       # if statements
THEN = 'THEN'
ELSE = 'ELSE'
ENDIF = 'ENDIF'

WHILE = 'WHILE'     # loops
UNTIL = 'UNTIL'
LOOP = 'LOOP'
FOR = 'FOR'
IN = 'IN'
ENDLOOP = 'ENDLOOP'
NEXT = 'NEXT'
BREAK = 'BREAK'

FUNC = 'FUNC'
ENDFUNC = 'ENDFUNC'    # functions
DO = 'DO'
RETURN = 'RETURN'


object_types = [
    STR,
    NUM,
    LIST,      # things that can be evaluated
    NONE,

    LIST_OBJ,
    STR_OBJ,
    NUM_OBJ,
    BOOL_OBJ,

    TRUE,
    FALSE,

    IDENTIFIER,
]

identifier_subtypes = [
    IDENTIFIER,

    STR_OBJ,
    NUM_OBJ,
    LIST_OBJ,    # things that aren't "specialised" - useful for
    BOOL_OBJ,    # attribute access names
    INDEX_OBJ,
]

expression_starters = [
    LPAREN,
    LBRACKET,

    ADD,
    SUB,

    COLON
]

builtins_tokens = [
    STR_OBJ,
    NUM_OBJ,
    LIST_OBJ,
    BOOL_OBJ,
    INDEX_OBJ,
]


class Token:
    def __init__(self, token_type, value,
                       lookahead_text='',
                       previous_text='',
                       line=None):
        self.type = token_type
        self.value = value
        self.lookahead = (previous_text
                          + lookahead_text).strip().split('\n')[0]
        self.line = line
        # print(self.type)

    def __repr__(self):
        return 'Token({}, {})'.format(self.type,
                                      repr(self.value))

    def __str__(self):
        return str(self.value)


reserved_keywords = {
    'String': Token(STR_OBJ, 'String'),
    'Number': Token(NUM_OBJ, 'Number'),
    'List': Token(LIST_OBJ, 'List'),
    'Boolean': Token(BOOL_OBJ, 'Boolean'),

    'join': Token(IDENTIFIER, 'join'),
    'show': Token(IDENTIFIER, 'show'),
    'type': Token(IDENTIFIER, 'type'),

    'if': Token(IF, 'if'),
    'then': Token(THEN, 'then'),
    'else': Token(ELSE, 'else'),
    'endif': Token(ENDIF, 'endif'),

    'while': Token(WHILE, 'while'),
    'loop': Token(LOOP, 'loop'),
    'for': Token(FOR, 'for'),
    'in': Token(IN, 'in'),
    'until': Token(UNTIL, 'until'),
    'endloop': Token(ENDLOOP, 'endloop'),
    'next': Token(NEXT, 'next'),
    'break': Token(BREAK, 'break'),

    'function': Token(FUNC, 'function'),
    'endfunction': Token(ENDFUNC, 'endfunction'),
    'do': Token(DO, 'do'),
    'return': Token(RETURN, 'return'),

    'true': Token(TRUE, 'true'),
    'false': Token(FALSE, 'false'),
    'none': Token(NONE, 'none'),
    }

whitespace = string.whitespace
digits = string.digits
letters = string.ascii_letters
letters_under = string.ascii_letters + '_'
letters_identifier = digits + letters_under
string_characters = (letters + digits + whitespace
                     + r'`!"£$%^&*()_-+={[}]:;@~#<,>.?€/'
                     + '\\')
arbitrary = '~arbitrary'
instance = 'instance'
