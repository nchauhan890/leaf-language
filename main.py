"""Main Leaf Lexer/Parser/Interpreter."""

import sys

import leaf_parser
import leaf_lexer
import leaf_interpreter

print()


"""
l = leaf_lexer.Lexer('''number << 2
a << number
b << 10 * a + 10 * number // 4
c << a - - b
''')"""
with open('demo.leaf', 'r') as f:
    text = f.read()

l = leaf_lexer.Lexer(text)
p = leaf_parser.Parser(l)
i = leaf_interpreter.Interpreter(p)

i.interpret()
# print(i.GLOBAL_SCOPE)



#######
# sys.exit(0)
#######
if __name__ == '__main__':
    result = ''
    GLOBAL = {}
    # lexer = Lexer('''
# 5 + 5
# 53 - 5
# 5 // 551
# 5 * 5
# 5091 // 5
# ''')
    # lexer = Lexer('(5 + 5) * 5')
    while True:
        def update_with(orig_dict, new_dict):
            for var, value in new_dict.items():
                orig_dict[var] = value

        try:
            text = input('>>> ')
            if text == 'exit':
                sys.exit()

            text = (text.replace('~~', str(result))
                    if result
                    else text.replace('~~', ''))
            # use as previous action

            if not bool(text):
                continue

            lexer = leaf_lexer.Lexer(text)
            parser = leaf_parser.Parser(lexer)
            interpreter = leaf_interpreter.Interpreter(parser)

            update_with(interpreter.GLOBAL_SCOPE, GLOBAL)

            result = interpreter.interpret()
            if result:
                print(result)

            update_with(GLOBAL, interpreter.GLOBAL_SCOPE)


        except KeyboardInterrupt as e:
            raise

        except TypeError as e:
            print('TypeError:', e)

        # except SyntaxError as e:
        #     print('SyntaxError:', e)

        except NameError as e:
            print('NameError:', e)

        except ZeroDivisionError as e:
            print('ZeroDivisionError', e)

        # except Exception as e:
        #     print('Exception:', e)

