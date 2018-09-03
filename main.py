"""Main Leaf Lexer/Parser/Interpreter."""

import sys

import leaf_parser
import leaf_lexer
import leaf_interpreter


"""
l = leaf_lexer.Lexer('''number << 2
a << number
b << 10 * a + 10 * number // 4
c << a - - b
''')

p = leaf_parser.Parser(l)
i = leaf_interpreter.Interpreter(p)

print(i.interpret())
print(i.global_scope)




#######
sys.exit()"""
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

        except SyntaxError as e:
            print('SyntaxError:', e)

        except Exception as e:
            print('Exception:', e)

