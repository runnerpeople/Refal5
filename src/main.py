#! python -v
# -*- coding: utf-8 -*-

from os.path import *
from src.lex_refal import *
from src.parser_refal import *
from src.parser_refal_type import *
from src.algorithm import *

TEST_DIRECTORY = join(dirname(dirname(__file__)), 'test_refal').replace("\\", "/")
DEBUG_MODE = True
NAME_FILE = "test10"

REFAL_TYPE = ".ref"
FILE_TYPE = ".type"

LINE_DELIMITER = "=================="

file_type = None
file_refal = None


try:
    file_refal = open(join(TEST_DIRECTORY, NAME_FILE + REFAL_TYPE).replace("\\", "/"), "r+", encoding="utf-8")
    if exists(join(TEST_DIRECTORY, NAME_FILE + FILE_TYPE).replace("\\", "/")):
        file_type = open(join(TEST_DIRECTORY, NAME_FILE + FILE_TYPE).replace("\\", "/"), "r+", encoding="utf-8")

except (FileNotFoundError, IOError) as e:
    sys.stderr.write(str(e))
    sys.exit(-1)

program = file_refal.read()

tips_program = None
if file_type is not None:
    tips_program = file_type.read()

lexer_refal = Lexer(program)

lexer_type = None
if tips_program is not None:
    lexer_type = Lexer(tips_program)

cur_token_refal = lexer_refal.next_token()
list_token_refal = [cur_token_refal]

if DEBUG_MODE:
    print(cur_token_refal)
while cur_token_refal.tag != DomainTag.Eop:
    cur_token_refal = lexer_refal.next_token()
    if DEBUG_MODE:
        print(cur_token_refal)
    list_token_refal.append(cur_token_refal)

if DEBUG_MODE:
    print(LINE_DELIMITER)

list_token_type = []
if lexer_type is not None:
    cur_token_type = lexer_type.next_token()
    list_token_type = [cur_token_type]

    if DEBUG_MODE:
        print(cur_token_type)
    while cur_token_type.tag != DomainTag.Eop:
        cur_token_type = lexer_type.next_token()
        if DEBUG_MODE:
            print(cur_token_type)
        list_token_type.append(cur_token_type)

file_refal.close()

if file_type is not None:
    file_type.close()

if DEBUG_MODE:
    print(LINE_DELIMITER)

parser_refal = ParserRefal(list_token_refal)
parser_refal.parse()

if DEBUG_MODE:
    print(LINE_DELIMITER)

if DEBUG_MODE:
    print(parser_refal.ast)

parser_refal.semantics()

if DEBUG_MODE:
    print(LINE_DELIMITER)

parser_refal_type = None
if list_token_type:
    parser_refal_type = ParserRefalType(list_token_type)
    parser_refal_type.parse()

    if DEBUG_MODE:
        pass

    # if DEBUG_MODE:
    #     print(parser_refal_type.ast)

    parser_refal_type.semantics()

if not parser_refal.isError and ((parser_refal_type is not None and not parser_refal_type.isError) or
                                 parser_refal_type is None):
    calculation = None
    if parser_refal_type is not None:
        calculation = Calculation(parser_refal.ast, parser_refal_type.ast)
    else:
        calculation = Calculation(parser_refal.ast, None)

