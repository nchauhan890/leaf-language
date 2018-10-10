import sys

import leaf_parser
import leaf_lexer
import leaf_types_interpreter as leaf_interpreter

print()


def update_with(orig_dict, new_dict):
    if type(orig_dict) == leaf_interpreter.ScopedSymbolTable:
        for var, value in new_dict.items():
                orig_dict.__setitem__(var, value, protected=True)
    else:
        for var, value in new_dict.items():
            orig_dict[var] = value


original_global_scope = leaf_interpreter.GLOBAL_SCOPE

if __name__ == '__main__':
    result = ''
    GLOBAL = {}
    interpreter = leaf_interpreter.Interpreter(None)
    interpreter.make_interactive()
    update_with(GLOBAL, leaf_interpreter.GLOBAL_SCOPE)
    # lexer = Lexer('''
# 5 + 5
# 53 - 5
# 5 // 551
# 5 * 5
# 5091 // 5
# ''')
    # lexer = Lexer('(5 + 5) * 5')
    while True:
        try:
            text = input('>>> ')
            if text == 'exit':
                sys.exit()

            if text.strip().startswith('open'):
                leaf_interpreter.GLOBAL_SCOPE = original_global_scope
                with open(text[4:].strip(), 'r') as f:
                    text = f.read()

            if text.strip() == 'scope':
                print(leaf_interpreter.current_scope)
                continue

            if not text.strip():
                continue

            lexer = leaf_lexer.Lexer(text)
            parser = leaf_parser.Parser(lexer)
            interpreter = leaf_interpreter.Interpreter(parser)

            update_with(leaf_interpreter.GLOBAL_SCOPE, GLOBAL)

            result = interpreter.interpret()
            # if result:
            #     print(result)

            update_with(GLOBAL, leaf_interpreter.GLOBAL_SCOPE)


        except KeyboardInterrupt as e:
            raise

        except TypeError as e:
            print('TypeError', e)

        except SyntaxError as e:
            print('SyntaxError', e)

        except NameError as e:
            print('NameError', e)

        except ZeroDivisionError as e:
            print('ZeroDivisionError', e)

        except FileNotFoundError as e:
            print('FileNotFoundError:', e)

        except RecursionError as e:
            print('RecursionError:', e)

        # except Exception as e:
        #     print('Exception:', e)
