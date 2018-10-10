"""AST Interpreter for Leaf."""

import sys
import decimal
import functools

from leaf_ast import *
from leaf_tokens import *


class ScopedSymbolTable:
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self.symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self.add_builtins()

    def __repr__(self):
        return 'ScopedSymbolTable:\n{}'.format('\n'.join(repr(k) + repr(v)
                                               for k, v in self.symbols.items()
                                               ))

    def lookup(self, name, single_scope=False):
        try:
            value = self.symbols[name]

        except KeyError:
            if single_scope:
                raise
            elif self.enclosing_scope is not None:
                value = self.enclosing_scope.lookup(name)
                # recursively go through enclosing scopes
            else:
                raise

        return value

    def __getitem__(self, key):
        # global current_scope
        # return self.lookup(key,
        #        single_scope=current_scope.scope_name == 'user function call')
        return self.lookup(key)

    def __setitem__(self, key, value, *, protected=False):
        if not protected and key in interpreter_globals:
            raise TypeError('cannot assign to protected name')
        self.symbols[key] = value

    def insert(self, key, value):
        self.__setitem__(key, value)

    def items(self):
        return self.symbols.items()

    def add_builtins(self):
        for name, obj in builtins.items():
            self[name] = obj

        if self.enclosing_scope is not None:
            for key in interpreter_globals:
                self.__setitem__(key, self.enclosing_scope[key],
                                 protected=True)

        else:
            for key, value in interpreter_globals.items():
                self.__setitem__(key, value, protected=True)

    def get_enclosing_scope_names(self):
        if self.enclosing_scope is None:
            return [self.scope_name]

        else:
            return ([self.scope_name]
                    + self.enclosing_scope.get_enclosing_scope_names())


class NodeParser:
    def parse(self, node):
        # print('parsing: {}'.format(node.__class__.__name__))
        if (isinstance(node, type)
            or isinstance(node, Function)):
            return node
        method = 'parse_{}'.format(node.__class__.__name__)
        parser = getattr(self, method, self.parsing_error)
        return parser(node)

    def parsing_error(self, node):
        raise TypeError('Couldn\'t find parse_{} method'
                        .format(node.__class__.__name__))

    def raise_error(self, error, message, obj, parse=False):
        if parse:
            obj = self.parse(obj)
        # cannot be called from this class directly as it doesn't have any
        # parsing methods defined!
        prefix = 'in line {}:\n{}\n'.format(obj.token.line,
                                            obj.token.lookahead)
        # add in the line + invalid code
        raise error(prefix + message) from None


class Interpreter(NodeParser):

    current_state = []

    def __init__(self, parser):
        self.parser = parser

    def interpret(self):
        self.abstract_syntax_tree = self.parser.parse()
        return self.parse(self.abstract_syntax_tree)

    def make_interactive(self):
        current_scope.__setitem__('__interactive__', true, protected=True)

    def parse_BinaryOperation(self, node):
        operator = node.op
        try:

            if operator.type == ADD:
                r = self.parse(node.left) + self.parse(node.right)

            elif operator.type == SUB:
                r = self.parse(node.left) - self.parse(node.right)

            elif operator.type == MUL:
                r = self.parse(node.left) * self.parse(node.right)

            elif operator.type == FLOORDIV:  # floor div
                r = self.parse(node.left) // self.parse(node.right)

            elif operator.type == DIV:       # normal div
                r = self.parse(node.left) / self.parse(node.right)


            elif operator.type == POWER:
                r = self.parse(node.left) ** self.parse(node.right)

            elif operator.type == MOD:
                r = self.parse(node.left) % self.parse(node.right)


            elif operator.type == EQUAL:
                r = self.parse(node.left) == self.parse(node.right)

            elif operator.type == N_EQUAL:
                r = self.parse(node.left) != self.parse(node.right)

            elif operator.type == L_EQUAL:
                r = self.parse(node.left) <= self.parse(node.right)

            elif operator.type == G_EQUAL:
                r = self.parse(node.left) >= self.parse(node.right)

            elif operator.type == LESS:
                r = self.parse(node.left) < self.parse(node.right)

            elif operator.type == GREATER:
                r = self.parse(node.left) > self.parse(node.right)



        except TypeError as e:  # unsupported operation
            # raise
            self.raise_error(TypeError, 'Invalid operation: {} {} {}'
                            .format(self.parse(node.left).__class__.__name__,
                                    operator.value,
                                    self.parse(node.right).__class__.__name__
                                    ),
                            node)

        else:
            # raise TypeError('Could not parse binary operation')
            if r is True:
                r = true
            elif r is False:
                r = false
            return r

    def parse_FunctionCall(self, node):
        # function = builtins.get(node.function)
        Interpreter.current_state.append('parse_FunctionCall')
        try:
            obj = self.parse(node.function_node)
            if type(node.function_node) == AttributeAccess:
                actual_obj = self.parse(node.function_node.left)
                # print(repr(actual_obj))

            elif isinstance(obj, BoundMethod):
                # print('found bound method')
                actual_obj = obj.instance

            elif isinstance(obj, Method):
                # print('found normal method')
                actual_obj = obj.cls

            if isinstance(obj, Method):
                base_class = obj.cls  # the class in which the method is found
                if not isinstance(actual_obj, type):
                    if node.args:
                        if not self.parse(node.args[0]) == actual_obj:
                            node.args.insert(0, actual_obj)
                    else:
                        node.args.insert(0, actual_obj)

                function = base_class.__namespace__[obj.value]

            else:
                function = current_scope[str(obj.value)]

        except KeyError:
            self.raise_error(NameError, "Could not find {}"
                             .format(str(self.parse(
                                    node.function_node).value)),
                             node.function_node,
                             parse=True)

        if function in builtin_types.values():
            function = function.function

        args = node.args
        new_args = {}
        modifiers = node.modifiers
        new_modifiers = {}
        flags = node.flags  # already string-only guaranteed by parser

        # if not isinstance(function, leaf_builtins.Function):
        #     raise TypeError('{} is not a function'.format(function
        #                                                   .__class__
        #                                                   .__name__))
        # print('\n'.join(str(i) for i in args))
        results = []
        for i, arg in enumerate(args):
            if type(arg) == IterableUnpacking:
                r = self.parse(arg)
                results.extend([arg for arg in r])
            else:
                results.append(arg)
        # print('\n\n\n', '\n'.join(str(i) for i in results))
        args = results

        if function:
            # print(function.arbitrary,
            #       function.arg_names,
            #       function.modifiers,
            #       function.flags, sep='\n')
            if function.arbitrary:
                if len(args) < len(function.arg_names):
                    self.expected('argument',
                                  function.arg_names[len(args)],
                                  function)
                # can't check for a maximum number of args if the number
                # is arbitrary
                i = 0

                for name in function.arg_names:
                    new_args[name] = args[i]  # the arbitrary args don't have
                    i += 1                    # an arg name

                new_args[arbitrary] = args[i:]
                # add the rest of the args to the arbitrary args category
                # use i from the enumeration
                # (already a list since args is a list)

            else:
                if len(args) < len(function.arg_names):
                    self.expected('argument',
                                  function.arg_names[len(args)],
                                  function)
                elif len(args) > len(function.arg_names):
                    self.unexpected('argument',
                                    self.parse(args[len(function.arg_names)]),
                                    function)

                for name, arg in zip(function.arg_names, args):
                    new_args[name] = arg


            for modifier, value in modifiers.items():
                if isinstance(self.parse(value), Boolean):
                    flags[modifier] = value
                    continue
                else:
                    new_modifiers[modifier] = value

                if modifier not in function.modifiers:
                    self.unexpected('modifier', modifier, function)

            for flag in flags:
                if flag not in function.flags:
                    self.unexpected('flag', flag, function)

            for flag in function.flags:
                if flag not in flags:
                    flags[flag] = false

            for name, arg in new_args.items():
                if isinstance(arg, list):
                    arg = [self.parse(i) for i in arg]
                    new_args[name] = arg
                else:
                    new_args[name] = self.parse(arg)

        try:
            r = function(new_args, modifiers, flags)
            #              dict      dict     dict

        except AttributeError:
            self.raise_error(TypeError, 'Unsupported function call {} ({})'
                             .format(node.token.value, node.function),
                             node)
        else:
            Interpreter.current_state.pop()
            if isinstance(r, (type(None), str, int, float,
                              list, dict, tuple, bool)):
                self.raise_error(TypeError, 'function returned python <{}>'
                                 .format(type(r).__name__),
                                 function)
            return r

    def parse_Number(self, node):
        return node

    def parse_String(self, node):
        return node

    def parse_Boolean(self, node):
        return node

    def parse_List(self, node):
        results = []
        for value in node.value:
            if type(value) == IterableUnpacking:
                results.extend(self.parse(value))
            else:
                results.append(self.parse(value))
        node.value = results
        return node

    def parse_IterableUnpacking(self, node):
        r = List(Token(LIST, [i for i in self.parse(node.expression)]))
        # node.expression must is either a List object or
        # a Variable object whose value is a list.
        # So parsing it returns the iterable.
        # Then we iterate over it
        return r

    def parse_UnaryOperation(self, node):
        operator = node.op.type
        if operator == ADD:
            return +self.parse(node.expression)

        elif operator == SUB:
            return -self.parse(node.expression)

        else:
            self.raise_error(TypeError, 'Could not parse unary operation',
                             node)

    def parse_StatementList(self, node):
        Interpreter.current_state.append('parse_StatementList')
        for child in node.children:
            # print('\n\n')
            if isinstance(child, Return):
                r = self.parse(child)
                Interpreter.current_state.pop()
                return r

            if isinstance(child, LoopControl):
                r = self.parse(child)
                # print('returned next', repr(r))
                Interpreter.current_state.pop()
                return r

            else:
                r = self.parse(child)
                if isinstance(r, LoopControl):
                    # handle next statements that occur in if statements
                    Interpreter.current_state.pop()
                    return r

                if (isinstance(child, FunctionCall)
                    and self.parse(child.function_node).value == 'show'):
                    r = none
                    continue

                if (not isinstance(r, NoneObject)
                    and current_scope['__interactive__']
                    and r is not None
                    and current_scope.scope_name != 'user function call'
                    and not isinstance(r, LoopControl)):
                    # print('printing:', repr(r))
                    print(r)
        Interpreter.current_state.pop()
        return r

    def parse_IfStatement(self, node):
        Interpreter.current_state.append('parse_IfStatement')
        r = none
        if bool(self.parse(node.expression)):
            r = self.parse(node.block)
            Interpreter.current_state.pop()
            # print('if statement returns', repr(r))
            return r  # discard any more clauses

        if node.elif_expressions:
            for expr, block in zip(node.elif_expressions,
                                   node.elif_blocks):
                if bool(self.parse(expr)):
                    r = self.parse(block)
                    Interpreter.current_state.pop()
                    return r  # discard any more elif/else clauses

        if node.else_block:
            r = self.parse(node.else_block)
        Interpreter.current_state.pop()
        return r

    def parse_WhileLoop(self, node):
        Interpreter.current_state.append('parse_WhileLoop')
        while bool(self.parse(node.expression)):
             self.parse(node.block)
        # simple parsing procedure: just keep parsing the block
        # until the expression doesn't evaluate to true
        Interpreter.current_state.pop()

    def parse_UntilLoop(self, node):
        Interpreter.current_state.append('parse_UntilLoop')
        while not bool(self.parse(node.expression)):
            self.parse(node.block)
        # use the same parsing as a while loop, but negate the
        # expression's evaluation
        Interpreter.current_state.pop()

    def parse_ForLoop(self, node):
        global current_scope
        Interpreter.current_state.append('parse_ForLoop')
        outer_scope = current_scope
        current_scope = ScopedSymbolTable('for loop',
                                          current_scope.scope_level + 1,
                                          current_scope)
        # 'outer scope' is the enclosing scope of the foor loop

        iterable = self.parse(node.iterable)
        # print('iterable', '\n'.join(repr(i) for i in iterable))
        iterator = iter(iterable)

        while True:
            try:
                args_ = next(iterator)
                if type(node.iterable) == IterableUnpacking:
                    args_ = [i for i in args_]
                else:
                    args_ = [args_]
            except StopIteration:
                break
            else:
                args = args_

            # print(repr(iterable), repr(node.iterable), sep='\n')
            # print('\n'.join(repr(x) for x in args))

            if len(args) != len(node.parameters):
                self.raise_error(NameError, '{} returns {} values per '
                                 'iteration'
                                 .format(iterable.__class__.__name__,
                                        len(args)),
                                 node.iterable)

            for i, (arg, param) in enumerate(zip(args, node.parameters)):
                #          ^ parameter name from for loop definition
                current_scope.__setitem__(param.value, self.parse(arg),
                                          protected=True)
            # print(current_scope)
            r = self.parse(node.block)
            # print(repr(r))
            if isinstance(r, LoopControl):
                if r.token.type == NEXT:
                    continue
                elif r.token.type == BREAK:
                    break

        for name, value in current_scope.items():
            outer_scope.__setitem__(name, value, protected=True)

        current_scope = outer_scope
        Interpreter.current_state.pop()
        # return r

    def parse_Empty(self, node):
        return None

    def parse_Assign(self, node):
        global current_scope
        if type(node.left) == AttributeAccess:
            obj, attr = self.parse(node.left.left), node.left.name
            obj.__namespace__[attr] = self.parse(node.right)

        else:
            name = node.left.value
            # cannot parse this as the variable doesn't actually exist yet
            current_scope[name] = self.parse(node.right)

    def parse_MultipleAssign(self, node):
        global current_scope
        variables = node.variables
        names = [var.expression.value
                 if type(var) == IterableUnpacking else var.value
                 for var in variables]
        args = []

        for arg in node.arguments:
            if type(arg) == IterableUnpacking:
                args.extend(self.parse(arg))
            else:
                args.append(self.parse(arg))

        original_length = len(args)
        unpacked = []
        normal = []
        accumulated_values = {}
        for var in variables:
            if type(var) == IterableUnpacking:
                unpacked.append(var.expression.value)
                accumulated_values[var.expression.value] = List(Token(LIST,
                                                                      []))
            else:
                normal.append(var.value)
                accumulated_values[var.value] = None

        if unpacked:
            each, last = divmod(len(args) - len(normal), len(unpacked))
            chunks = [each for _ in range(len(unpacked))]
            for i in range(last):
                chunks[i] += 1

        if len(args) < len(normal):
            self.raise_error(TypeError, 'expected {} values, got {}'
                             .format(len(normal), len(args)),
                             node)

        for var in variables:
            if type(var) == IterableUnpacking:
                for _ in range(chunks.pop(0)):
                    (accumulated_values[var.expression.value]
                        .value.extend(self.parse(args.pop(0))))
            else:
                accumulated_values[var.value] = self.parse(args.pop(0))

        if args:  # if all of the values haven't been used up
            self.raise_error(TypeError, 'expected {} values, got {}'
                             .format(len(normal), original_length),
                             node)

        for name, value in accumulated_values.items():
            current_scope[name] = value

    def parse_FunctionDefinition(self, node):
        global current_scope
        arg_names = [var.value for var in node.arg_names]
        modifiers = {k: self.parse(v)
                     for k, v in node.modifiers.items()}
        flags = node.flags
        function = UserFunction(token     = node.token,
                                arg_names = arg_names,
                                arbitrary = node.arbitrary,
                                modifiers = modifiers,
                                flags     = flags,
                                body      = node.body)
        current_scope[node.value] = function

    def parse_Variable(self, node):
        global current_scope
        name = node.value

        try:
            value = current_scope[name]
        except KeyError:
            self.raise_error(NameError, "in line {}:\nCould not find {}"
                             .format(node.token.line, repr(name)),
                             node)

        return value

    def parse_Return(self, node):
        global current_scope
        if not any(name == 'user function call'
                   for name in current_scope.get_enclosing_scope_names()):
            self.raise_error(SyntaxError, 'in line {}: {}\n\'return\' must '
                             'be placed inside a function'
                             .format(node.token.line,
                                     node.token.lookahead),
                             node)

        return self.parse(node.expression)

    def parse_LoopControl(self, node):
        f = not any(i in Interpreter.current_state
                   for i in ('parse_ForLoop',
                             'parse_WhileLoop', 'parse_UntilLoop'))
        # print('\n\nparsing LoopControl:', f)
        if f:
            self.raise_error(SyntaxError, '\'next\' must be within a loop',
                             node)
        return node

    def parse_AttributeAccess(self, node):
        obj = self.parse(node.left)
        attr = node.name
        # print(obj.__namespace__)

        try:
            attribute = obj.__namespace__[attr]
        except KeyError:
            if not isinstance(obj, type):
                obj = obj.__class__
            self.raise_error(NameError, "Could not find attribute {} of {}"
                             .format(repr(attr), obj.__name__),
                             node.left, parse=True)

        return attribute

    def parse_NoneObject(self, node):
        try:
            self.raise_error(TypeError,
                             'something returned python <NoneObject>',
                             node)
        except AttributeError:
            raise TypeError('something returned python <NoneObject>')

    def parse_NoneObject(self, node):
        return node

    def parse_Indexed(self, node):
        return node

    def parse_Parallel(self, node):
        return node

    def parse_Chain(self, node):
        return node

    def unexpected(self, name, value, obj):
        self.raise_error(SyntaxError, 'unexpected {}: {}'.format(name, value),
                         obj)

    def expected(self, category, name, obj):
        self.raise_error(SyntaxError, 'expected {}: {}'.format(category, name),
                         obj)


# builtin type base class




class MetaType(type):

    __namespace__ = {}

    def __str__(cls):
        return '<type {} from built-ins>'.format(cls.__name__)

    def __eq__(cls, other):
        if (isinstance(cls, type)
            and isinstance(other, type)):
            return true if cls.__name__ == other.__name__ else false
        return false

    def __ne__(cls, other):
        if (isinstance(cls, type)
            and isinstance(other, type)):
            return true if cls.__name__ == other.__name__ else false
        return false

    def __hash__(cls):
        return hash(cls.__name__)

    def not_implemented(*args, **kwargs):
        return NotImplemented

    def return_false(*args, **kwargs):
        return false

    __lt__ = __le__ = return_false
    __gt__ = __ge__ = return_false
    __add__ = __radd__ = not_implemented
    __sub__ = __rsub__ = not_implemented
    __mul__ = __rmul__ = not_implemented
    __truediv__ = __rtruediv__ = not_implemented
    __floordiv__ = __rfloordiv__ = not_implemented
    __pow__ = __rpow__ = not_implemented
    __mod__ = __rmod__ = not_implemented
    __pos__ = __neg__ = not_implemented


class Type(Interpreter, metaclass=MetaType):

    def __init_subclass__(cls):
        # cls.value = cls.__name__
        cls.__namespace__ = getattr(cls, '__namespace__', {})

    def __init__(self, token, *,
                error_msg='{}',
                expected_type=None,
                expected_value=None):
        self.token = token
        self.value = token.value
        # print(self.token)
        if '{}' not in error_msg:
            raise TypeError()
        if expected_type:
            if not isinstance(self.value, expected_type):
                raise TypeError(error_msg.format(self.value
                                                 .__class__.__name__))
        elif isinstance(expected_value, (tuple, list)):
            if self.value not in expected_value:
                raise TypeError(error_msg.format(self.value
                                                 .__class__.__name__))

        elif expected_value:
            if self.value != expected_value:
                raise TypeError(error_msg.format(self.value
                                                 .__class__.__name__))

    def zip_longest(self, iterables, pad):
        def gen_values(i):
            for item in i:
                yield item
            while True:
                yield pad
        generators = [gen_values(i) for i in iterables]
        for _ in range(max(len(i) for i in iterables)):
            yield [next(generator) for generator in generators]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.token))

    def __str__(self):
        if isinstance(self, (List)):
            return '[{}]'.format(', '.join([str(self.parse(i))
                                            for i in self.value]))

        elif isinstance(self, Indexed):
            return 'Indexed[{}]'.format(str(self.iterable))

        elif isinstance(self, (Parallel, Chain)):
            return '{}[{}]'.format(self.__class__.__name__,
                                    ', '.join([str(i)
                                         for i in self.iterables]))

        elif isinstance(self, Boolean):
            return 'false' if int(self.value) == 0 else 'true'

        return str(self.value)

    def unsupported_binary_op(self, op, obj1, obj2):
        raise TypeError('Invalid operation: {} {} {}'
                        .format(obj1.__class__.__name__,
                                op,
                                obj2.__class__.__name__))

    def unsupported_unary_op(self, op, obj):
        raise TypeError('Invalid operation: {} {}'
                        .format(op, obj.__class__.__name__))

    # binary operation methods (arithmetic)

    def __add__(self, other):

        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(NUM, val_1 + val_2))

        elif (isinstance(other, String)
            and isinstance(self, String)):
            val_1 = str(self)
            val_2 = str(other)
            return String(Token(STR, val_1 + val_2))

        elif (isinstance(other, List)
              and isinstance(self, List)):
            values_1 = self.value
            values_2 = other.value
            new_values = values_1 + values_2
            return List(Token(LIST, new_values))

        else:
            # self.unsupported_binary_op('+', self, other)
            return NotImplemented

    def __sub__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(NUM, val_1 - val_2))

        else:
            # self.unsupported_binary_op('-', self, other)
            return NotImplemented

    def __mul__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            return Number(Token(NUM, val_1 * val_2))

        elif (isinstance(other, String)
              and isinstance(self, Number)):

            if not self.is_integer():
                raise TypeError('cannot multiply String by non-integer Number')

            val_1 = int(self.value)
            val_2 = other.value
            return String(Token(STR, val_1 * val_2))

        elif (isinstance(other, Number)
              and isinstance(self, String)):

            if not other.is_integer():
                raise TypeError('cannot multiply String by non-integer Number')

            val_1 = self.value
            val_2 = int(other.value)
            return String(Token(STR, val_1 * val_2))

        # elif (isinstance(other, Function)
        #       and isinstance(self, Function)):
        #     return CompositeFunction(self, other)

        elif (isinstance(other, List)
              and isinstance(self, Number)):

            if not self.is_integer():
                raise TypeError('cannot multiply List by non-integer Number')

            val_1 = int(self.value)  # number
            values_2 = other.value   # list
            return List(Token(LIST, values_2 * val_1))

        elif (isinstance(other, Number)
              and isinstance(self, List)):

            if not other.is_integer():
                raise TypeError('cannot multiply List by non-integer Number')

            values_1 = self.value     # list
            val_2 = int(other.value)  # number
            return List(Token(LIST, values_1 * val_2))

        else:
            # self.unsupported_binary_op('*', self, other)
            return NotImplemented

    def __truediv__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if float(val_2) == 0.0:
                raise ZeroDivisionError('attempted division by zero')
            return Number(Token(NUM, val_1 / val_2))

        else:
            # self.unsupported_binary_op('/', self, other)
            return NotImplemented
    def __floordiv__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            val_2 = other.value
            if float(val_2) == 0.0:
                raise ZeroDivisionError('attempted floor division by zero')
            return Number(Token(NUM, val_1 // val_2))

        else:
            # self.unsupported_binary_op('//', self, other)
            return NotImplemented

    def __pow__(self, other):
        if (isinstance(other, Number)
            and isinstance(self, Number)):
            val_1 = self.value
            if float(val_1) == 0.0:
                raise ZeroDivisionError('attempted raising zero '
                                        'to a negative power')
            val_2 = other.value
            return Number(Token(NUM, val_1 ** val_2))

        else:
            # self.unsupported_binary_op('^', self, other)
            return NotImplemented

    def __mod__(self, other):
        if (isinstance(self, Number)
            and isinstance(other, Number)):
            val_1 = self.value
            val_2 = other.value
            if float(val_2) == 0.0:
                raise ZeroDivisionError('attempted modulo by zero')
            return Number(Token(NUM, val_1 % val_2))

    # Comparison methods

    def __eq__(self, other):
        if (isinstance(other, (String, Number, Boolean, List))
            and isinstance(self, (String, Number, Boolean, List))):
            val_1 = self.value
            val_2 = other.value
            if val_1 == val_2:
                r = true
            else:
                r = false

        elif (isinstance(other, (Indexed, Parallel))
              and isinstance(self, (Indexed, Parallel))):
            r = other.value == self.value and type(other) == type(self)
            r = true if r else false

        elif (isinstance(other, NoneObject)
              and isinstance(self, NoneObject)):
            r = true
            # 2 nones must be the same

        else:
            # self.unsupported_binary_op('=', self, other)
            r = false
            # equality must always true or false, so anything unsupported
            # is obviously false
        for obj in (self, other):
            if type(obj) not in builtin_types:
                try:
                    func = obj.__namespace__['__equal__']
                except KeyError:
                    continue
                else:
                    instance_arg = func.arg_names[0]
                    r = func({instance_arg: obj}, {}, {})
                    break
        return r


    def __ne__(self, other):
        if (isinstance(other, (String, Number, Boolean,
                               List))
            and isinstance(self, (String, Number, Boolean,
                                  List))):
            val_1 = self.value
            val_2 = other.value
            if val_1 != val_2:
                r = true
            else:
                r = false

        elif (isinstance(other, (Indexed, Parallel))
              and isinstance(self, (Indexed, Parallel))):
            r = other.value != self.value and type(other) == type(self)
            r = true if r else false

        elif (isinstance(other, NoneObject)
              and isinstance(self, NoneObject)):
            r = false
            # 2 nones can't not be equal

        else:
            # self.unsupported_binary_op('!', self, other)
            r = false
            # equality must always true or false, so anything unsupported
            # is obviously false
        for obj in (self, other):
            if type(obj) not in builtin_types:
                try:
                    func = obj.__namespace__['__unequal__']
                except KeyError:
                    continue
                else:
                    instance_arg = func.arg_names[0]
                    r = func({instance_arg: obj}, {}, {})
                    break
        return r

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
            # self.unsupported_binary_op('<', self, other)
            return NotImplemented

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
            # self.unsupported_binary_op('>', self, other)
            return NotImplemented

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
            # self.unsupported_binary_op('<=', self, other)
            return NotImplemented

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
            # self.unsupported_binary_op('>=', self, other)
            return NotImplemented

    # Unary operation methods

    def __neg__(self):
        if isinstance(self, Number):
            return Number(Token(self.token.type, -self.value))

        else:
            # self.unsupported_unary_op('+', self)
            return NotImplemented

    def __pos__(self):
        if isinstance(self, Number):
            return Number(Token(self.token.type, +self.value))

        else:
            # self.unsupported_unary_op('+', self)
            return NotImplemented

    def __hash__(self):
        return hash(self.token)

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__
    __rfloordiv__ = __floordiv__
    __rpow__ = __pow__
    __rmod__ = __mod__

    def __bool__(self):
        if isinstance(self, NoneObject):
            return False
        return bool(self.value)

    def __len__(self):
        if isinstance(self, Number):
            return len(str(self.value).replace('.', ''))
        return len(self.value)

    def __getitem__(self, key):
        return str(self.value)[key]

    def __iter__(self):
        # Make sure to yield a List object if necessary!
        if isinstance(self, Boolean):
            raise TypeError('Boolean is not iterable')

        elif isinstance(self, Indexed):
            count = self.start
            # not using enumerate() as a custom increment may be needed
            for item in self.iterable:
                # assuming the 'self' already has its own implementation
                # of iteration as indexed takes any iterable
                if self.unpack:
                    yield List(Token(LIST, [count, *item]))
                else:
                    yield List(Token(LIST, [count, item]))
                count = count + self.increment

        elif isinstance(self, Parallel):
            if self.short:
                gen = zip(*self.iterables)
            else:
                gen = self.zip_longest(self.iterables, self.pad)
            for items in gen:
                # 'items' is a generic python list/tuple
                # so needs to be converted into a Leaf List
                yield List(Token(LIST, [*items]))

        elif isinstance(self, Chain):
            for iterable in self.iterables:
                for item in iterable:
                    yield item


        elif isinstance(self, Number):
            for digit in str(self.value).replace('.', ''):
                # remove decimal point, if one exits
                # and return a Number containing the digit
                # (allows operations to be performed on it)
                if not digit.isdigit():
                    raise TypeError('digits of a number must be numbers')
                yield Number(Token(NUM, decimal.Decimal(digit)))

        elif isinstance(self, List):
            for item in self.value:
                # items are already generic Leaf types
                yield item

        elif isinstance(self, String):
            for char in self.value:
                yield String(Token(STR, char))

        else:
            raise TypeError('{} is not iterable'.format(
                            self.__class__.__name__))


# builtin function base class


class Function(Type):
    def __init__(self, *,
                 token,            # token
                 arg_names=None,   # list
                 arbitrary=False,  # True/False
                 modifiers=None,     # dict
                 flags=None):        # dict
        self.token = token
        self.value = token.value

        self.arbitrary = arbitrary

        self.arg_names = arg_names or []
        self.modifiers = modifiers or {}
        self.flags = flags or []

        # self.__namespace__ = {}

    # this method will must be overriden, trusting subclass
    # to have it implemented
    def __call__(self, *args):
        try:
            raise TypeError('unsupported function: {}'
                            .format(self.value))
        except AttributeError:
            raise TypeError('unsupported function') from None

    def __str__(self):
        return '<function {} from built-ins>'.format(self.value)

    def get_modifier(self, modifiers, name):
        return modifiers.get(name, self.modifiers[name])
        # try to get the modifier from the function call, and fall
        # back on the function's default value

    def __hash__(self):
        return hash(self.value)


# object method types

class Method(Function):
    def __init__(self, func, cls, arg_names=None,
                                  arbitrary=False,
                                  modifiers=None,
                                  flags=None):
        self.func = func
        self.cls = cls

        if arg_names is None:
            arg_names = [instance]
        else:
            arg_names.insert(0, instance)
        super(Method, self).__init__(token     = Token(IDENTIFIER,
                                                        func.__name__),
                                      arg_names = arg_names,
                                      arbitrary = arbitrary,
                                      modifiers = modifiers,
                                      flags     = flags)

    def __str__(self):
        return '<method {} of {} type>'.format(self.value,
                                               self.cls.__name__)

    def __call__(self, args, modifiers, flags):
        return self.func(self, args, modifiers, flags)


class BoundMethod(Method):
    def __init__(self, obj, method):
        method.arg_names.pop(0)
        super(BoundMethod, self).__init__(func = method.func,
                                     cls       = method.cls,
                                     arg_names = method.arg_names,
                                     arbitrary = method.arbitrary,
                                     modifiers = method.modifiers,
                                     flags     = method.flags)
        self.instance = obj

    def __str__(self):
        return '<bound method {} of {} type>'.format(self.value,
                                               self.cls.__name__)

    def __call__(self, args, modifiers, flags):
        return self.func(self, args, modifiers, flags)


def objMethod(cls, *, arg_names=None,
                   arbitrary=False,
                   modifiers=None,
                   flags=None):

    def wrapper(func):
        return Method(func, cls, arg_names, arbitrary, modifiers, flags)

    return wrapper


# user-defined functions

class UserFunction(Function):
    def __init__(self, *,
                 token,
                 arg_names = None,
                 arbitrary = None,
                 modifiers = None,
                 flags     = None,
                 body):
        self.body = body
        if arbitrary:
            self.arbitrary_name = arbitrary
            arbitrary = True
        else:
            self.arbitrary_name = None
            arbitrary = False

        super(UserFunction, self).__init__(token     = token,
                                       arg_names = arg_names,
                                       arbitrary = arbitrary,
                                       modifiers = modifiers,
                                       flags     = flags)

    def __call__(self, args, modifiers, flags):
        global current_scope
        outer_scope = current_scope
        current_scope = ScopedSymbolTable('user function call',
                                          outer_scope.scope_level + 1,
                                          outer_scope)
        # print('entered scope:', current_scope.scope_name,
        #       current_scope.scope_level)

        current_scope[self.token.value] = self

        for name in self.modifiers.keys():
            modifiers[name] = self.get_modifier(modifiers, name)

        if self.arbitrary:
            arbitrary_args = args[arbitrary]
            del args[arbitrary]

        for name in self.arg_names:
            current_scope[name] = self.parse(args[name])

        for name, value in flags.items():
            current_scope[name] = value

        for name, value in modifiers.items():
            current_scope[name] = value

        if self.arbitrary:
            current_scope[self.arbitrary_name] = List(Token(LIST,
                                                      arbitrary_args))

        # print('the scope contains:', str(current_scope), '\n\n\n')

        # print(args, end='\n\n')
        # print(arbitrary_args, end='\n\n')
        # print(modifiers, end='\n\n')
        # print(self.modifiers, end='\n\n')
        # print(flags, end='\n\n')
        # print(current_scope)
        return_value = self.parse(self.body)
        # the function returns something usually

        # print(current_scope)

        # for name, value in current_scope.items():
        #     outer_scope[name] = value

        # print('left scope:', current_scope.scope_name,
        #       current_scope.scope_level)
        current_scope = outer_scope

        return return_value

    def __str__(self):
        return '<user-defined function {}>'.format(self.value)


# builtin functions


class ReadOnly: pass


class NoneObject(Type):
    def __init__(self, token):
        self.token = token
        self.value = token.value


none = NoneObject(Token(NONE, 'none'))


class ShowFunction(Function):
    def __init__(self):
        super(ShowFunction,
              self).__init__(token   = Token(IDENTIFIER, 'show'),
                             arbitrary = True,
                             modifiers = {
                                'end': String(Token(STR, '\n')),
                                'sep': String(Token(STR, ' '))
                             },
                             flags     = ['comma_sep',
                                          'no_newline',
                                          'no_return'])

    def __call__(self, args, modifiers, flags):
        # print(args)
        # print(modifiers)
        # print(flags)
        if len(args[arbitrary]) > 0:
            end = str(self.parse(self.get_modifier(modifiers, 'end')))
            # default newline \n
            sep = str(self.parse(self.get_modifier(modifiers, 'sep')))
            # default space char

            result = ''

            if self.parse(flags['comma_sep']):
                sep = ', '
            if self.parse(flags['no_newline']):
                end = end.rstrip('\n')

            for arg in args[arbitrary][:-1]:
                result += str(self.parse(arg)) + sep     # add sep char

            arg = args[arbitrary][-1]
            result += str(self.parse(arg)) + end        # add end char

            sys.stdout.write(result)
            if not flags['no_return']:
                return String(Token(STR, result))
        return none


class JoinFunction(Function):
    def __init__(self):
        super(JoinFunction,
              self).__init__(token     = Token(IDENTIFIER, 'join'),
                             arbitrary = True,
                             modifiers = {
                                'end': String(Token(STR, '')),
                                'sep': String(Token(STR, '')),
                                'start': String(Token(STR, ''))
                             },
                             flags     = ['comma_sep'])

    def __call__(self, args, modifiers, flags):
        result = ''
        if len(args[arbitrary]) > 0:
            start = str(self.parse(self.get_modifier(modifiers, 'start')))
            # default none
            sep = str(self.parse(self.get_modifier(modifiers, 'sep')))
            # default none
            end = str(self.parse(self.get_modifier(modifiers, 'end')))
            # default none

            if self.parse(flags['comma_sep']):
                sep = ', '

            result = start + str(self.parse(args[arbitrary][0]))

            if len(args[arbitrary]) > 1:
                for arg in args[arbitrary][1:]:
                    result += sep + str(self.parse(arg))
            result += end

        return String(Token(STR, result))


class TypeFunction(Function):
    def __init__(self):
        super(TypeFunction,
              self).__init__(token     = Token(IDENTIFIER, 'type'),
                             arg_names = ['object'])

    def __call__(self, args, modifiers, flags):
        t = type(self.parse(args['object']))
        if t == MetaType:
            return Type
        return t


class IndexedFunction(Function):
    def __init__(self):
        super(IndexedFunction,
              self).__init__(token     = Token(IDENTIFIER, 'Indexed'),
                             arg_names = ['iterable'],
                             modifiers = {
                                 'start': Number(Token(NUM,
                                                 decimal.Decimal(0))),
                                 'increment': Number(Token(NUM,
                                                     decimal.Decimal(1)))
                                 },
                             flags     = ['unpack'])

    def __call__(self, args, modifiers, flags):
        start = self.get_modifier(modifiers, 'start')
        increment = self.get_modifier(modifiers, 'increment')
        iterable = self.parse(args['iterable'])
        return Indexed(iterable,
                       start     = start,
                       increment = increment,
                       unpack    = flags['unpack'])


class ParallelFunction(Function):
    def __init__(self):
        super(ParallelFunction,
              self).__init__(token     = Token(IDENTIFIER, 'Parallel'),
                             arg_names = ['iterable'],
                             arbitrary = True,
                             modifiers = {
                                 'pad': none
                                 },
                             flags     = ['short'])

    def __call__(self, args, modifiers, flags):
        pad = self.get_modifier(modifiers, 'pad')
        short = flags['short']
        iterables = [self.parse(args['iterable']),
                     *[self.parse(i) for i in args[arbitrary]]]
        return Parallel(iterables,
                        short=short,
                        pad=pad)


class ChainFunction(Function):
    def __init__(self):
        super(ChainFunction,
              self).__init__(token     = Token(IDENTIFIER, 'Chain'),
                             arg_names = ['iterable'],
                             arbitrary = True)

    def __call__(self, args, modifiers, flags):
        iterables = [self.parse(args['iterable']),
                     *[self.parse(i) for i in args[arbitrary]]]
        return Chain(iterables)


class StringFunction(Function):
    def __init__(self):
        super(StringFunction,
              self).__init__(token     = Token(STR_OBJ, 'String'),
                             arg_names = ['value'])

    def __call__(self, args, modifiers, flags):
        return String(Token(STR, str(self.parse(args['value']))))


class NumberFunction(Function):
    def __init__(self):
        super(NumberFunction,
              self).__init__(token     = Token(NUM_OBJ, 'Number'),
                             arg_names = ['value'])

    def __call__(self, args, modifiers, flags):
        result = ''   # similar to lexer here to check for a num format
        string = self.parse(args['value'])
        if isinstance(string, Number):
            return Number(Token(NUM, decimal.Decimal(float(string))))
        string = str(string).strip('\n ')
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

        if pos < len(string):
            raise TypeError('invalid value to convert to Number')

        return Number(Token(NUM, decimal.Decimal(result)))


class ListFunction(Function):
    def __init__(self):
        super(ListFunction,
              self).__init__(token     = Token(LIST_OBJ, 'List'),
                             arbitrary = True)

    def __call__(self, args, modifiers, flags):
        return List(Token(LIST, args[arbitrary]))


class BooleanFunction(Function):
    def __init__(self):
        super(BooleanFunction,
              self).__init__(token     = Token(BOOL_OBJ, 'Boolean'),
                             arg_names = ['value'])

    def __call__(self, args, modifiers, flags):
        if bool(args['value']):
            return Boolean(Token(TRUE, 'true'))
        return Boolean(Token(FALSE, 'false'))


# class CompositeFunction(Function):
#     def __init__(self, function_1, function_2):
#         self.function_1 = function_1
#         self.function_2 = function_2
#         self.arbitrary = function_1.arbitrary  # or function_2.arbitrary
#         self.arg_names = function_1.arg_names
#         self.flags = function_1.flags
#         self.modifiers = function_1.modifiers
#         self.token = Token(IDENTIFIER, function_1.name + function_2.name)
#         self.name = self.token.value

#     def __call__(self, args, modifiers, flags):
#         result_1 = [self.function_1(args, modifiers, flags)]
#         if not all(i is not None for i in result_1):
#             raise TypeError('CompositeFunction: first function did not '
#                             'return value to pass to second')
#         caller = FunctionCall(function  = self.function_2.name,
#                               args      = result_1,
#                               modifiers = {},
#                               flags     = [])
#         result_2 = self.parse(caller)
#         return result_2

#     def __getitem__(self, key): return object.__getitem__(key)



# builtin types


class List(Type):

    function = ListFunction()

    def __init__(self, token):
        msg = 'expected python <list> type, got <{}>'
        # print(type(token.value))
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=list)
        self.__namespace__ = {
            'add': BoundMethod(self, add),
            'remove': BoundMethod(self, remove)
            }


@objMethod(List, arg_names=['value'], flags=['copy'])
def add(self, args, modifiers, flags):
    if not isinstance(args[instance], List):
        raise TypeError('expected List type, got {}'
                        .format(type(args[instance]).__name__))
    if flags['copy']:
        values = args[instance].value
        values.append(args['value'])
        return List(Token(LIST, values))
    else:
        args[instance].value.append(args['value'])
        return none


@objMethod(List, arg_names=['index'], flags=['copy'])
def remove(self, args, modifiers, flags):
    obj = args[instance]
    index = args['index']
    if (not isinstance(index, Number)
        # and not index.__namespace__['integer']({instance: index}, {}, {})):
        and not call_method(obj.__class__, 'integer', instance=obj)):
        raise TypeError('List index must be an integer Number')
    if not isinstance(obj, List):
        raise TypeError('expected List type, got {}'
                        .format(type(obj).__name__))
    if flags['copy']:
        values = obj.value
        values.pop(int(index))
        return List(Token(LIST, values))
    else:
        args[instance].value.pop(int(index))
        return none


List.__namespace__ = {
    'add': add,
    'remove': remove,
    }


class Number(Type):

    function = NumberFunction()

    def __init__(self, token):
        msg = 'expected python <decimal.Decimal> type, got <{}>'
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=decimal.Decimal)
        for name, func in self.__class__.__namespace__.items():
            try:
                self.__namespace__[name] = BoundMethod(self, func)
            except NameError:
                continue

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def is_integer(self):
        return int(self) == float(self)


@objMethod(Number)
def integer(self, args, modifiers, flags):
    value = args[instance]
    if not isinstance(value, Number):
        raise TypeError('expected Number type, got {}'
                        .format(type(value).__name__))
    return true if value.is_integer() else false


Number.__namespace__ = {
    'integer': integer
    }


class Boolean(Number):

    function = BooleanFunction()

    def __init__(self, token):
        msg = 'expected python <str: \'true\' or \'false\'> type, got <{}>'
        if token.type == TRUE:
            token = Token(NUM, decimal.Decimal(1))
        elif token.type == FALSE:
            token = Token(NUM, decimal.Decimal(0))
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=decimal.Decimal)


true = Boolean(Token(TRUE, 'true'))
false = Boolean(Token(FALSE, 'false'))


class String(Type):

    function = StringFunction()

    def __init__(self, token):
        msg = 'expected python <str> type, got <{}>'
        Type.__init__(self, token,
                            error_msg=msg,
                            expected_type=str)

        namespace = {}
        for name, func in self.__class__.__namespace__.items():
            try:
                self.__namespace__[name] = BoundMethod(self, func)
                namespace[name] = BoundMethod(self, func)
            except (NameError, AttributeError):
                continue
                # dont add if the name hasn't been defined yet:
                # this may occur in method definitions
        self.__namespace__['__namespace__'] = namespace


@objMethod(String, flags=['in_place'])
def uppercase(self, args, modifiers, flags):
    if not isinstance(args[instance], String):
        raise TypeError('expected String type, got {}'
                        .format(type(args[instance]).__name__))
    if flags['in_place']:
        args[instance].value = args[instance].value.upper()
        return none
    else:
        return String(Token(STR, args[instance].value.upper()))


@objMethod(String, flags=['in_place'])
def lowercase(self, args, modifiers, flags):
    if not isinstance(args[instance], String):
        raise TypeError('expected String type, got {}'
                        .format(type(args[instance]).__name__))
    if flags['in_place']:
        args[instance].value = args[instance].value.lower()
        return none
    else:
        return String(Token(STR, args[instance].value.lower()))


@objMethod(String,
           arbitrary = True,
           modifiers = {
              'end': String(Token(STR, '')),
              'sep': String(Token(STR, '')),
              'start': String(Token(STR, ''))
           },
           flags     = ['comma_sep'])
def join(self, args, modifiers, flags):
    if not isinstance(args[instance], String):
        raise TypeError('expected String type, got {}'
                        .format(type(args[instance]).__name__))
    modifiers['sep'] = args['instance']
    del args['instance']
    return JoinFunction()(args, modifiers, flags)
    # don't pass self in here as the JoinFunction instance takes its place

String.__namespace__ = {
    'uppercase': uppercase,
    'lowercase': lowercase,
    'join': join
    }


class Indexed(Type):

    function = IndexedFunction()

    def __init__(self, iterable,
                 start=None,
                 increment=None,
                 unpack=False):

        if start is None:
            start = Number(Token(NUM, decimal.Decimal(0)))
        # if not isinstance(start, Number):
        #     raise TypeError('expected Number type for \'start\', got {}'
        #                     .format(start.__class__.__name__))

        if increment is None:
                increment = Number(Token(NUM, decimal.Decimal(0)))
        # if not isinstance(increment, Number):
        #     raise TypeError('expected Number type for \'increment\', '
        #                     'got {}'.format(increment.__class__.__name__))

        Type.__init__(self, iterable)
        self.start = start
        self.increment = increment
        self.unpack = bool(unpack)
        self.iterable = iterable
        # initialise the object as if it were any other object,
        # but include 'self.iterable' which holds the actual object
        # which should be an iterable


class Parallel(Type):

    function = ParallelFunction()

    def __init__(self, iterables,
                 short=False,
                 pad=None):
        Type.__init__(self, List(Token(LIST, iterables)))
        self.iterables = iterables
        self.short = bool(short)
        self.pad = pad if pad is not None else none


class Chain(Type):

    function = ChainFunction()

    def __init__(self, iterables):
        Type.__init__(self, List(Token(LIST, iterables)))
        self.iterables = iterables


builtins = {
    'show': ShowFunction(),
    'join': JoinFunction(),
    'type': TypeFunction(),

    'Boolean': Boolean,
    'String': String,
    'Number': Number,
    'List': List,
    'Type': Type,

    'Indexed': IndexedFunction(),
    'Parallel': ParallelFunction(),
    'Chain': ChainFunction(),

    'true': true,
    'false': false,
    }


interpreter_globals = {
    '__interactive__': false,
}


builtin_types = {
    'String': String,
    'Number': Number,
    'List': List,
    'Boolean': Boolean,

    'Indexed': Indexed,
    'Parallel': Parallel,
    'Chain': Chain,
    }

GLOBAL_SCOPE = ScopedSymbolTable('global', 1)
current_scope = GLOBAL_SCOPE


def call_method(obj, method_name, args=None,
                modifiers=None, flags=None, instance=None):
    args = args or {}
    modifiers = modifiers or {}
    flags = flags or {}
    if instance is not None:
        args[instance] = instance
    try:
        f = obj.__namespace__[method_name]
        modifiers = f.modifiers
        flags = f.flags
        r = f(args, modifiers, flags)
    except KeyError as e:
        raise AttributeError('could not find attribute \'{}\' of {}'
                             .format(method_name,
            TypeFunction()({'object': obj}, {}, {}).__name__)) from None
    else:
        return r
