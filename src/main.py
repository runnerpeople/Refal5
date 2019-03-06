#! python -v
# -*- coding: utf-8 -*-

from os.path import *
from src.lex_refal import *
from src.parser_refal import *
from src.parser_refal_type import *
from src.algorithm import *

TEST_DIRECTORY = join(dirname(dirname(__file__)), 'test_refal').replace("\\", "/")
DEBUG_MODE = True
NAME_FILE = "test8"

REFAL_TYPE = ".ref"
FILE_TYPE = ".type"

LINE_DELIMITER = "=================="

file_type = None
file_refal = None


try:
    file_refal = open(join(TEST_DIRECTORY, NAME_FILE + REFAL_TYPE).replace("\\", "/"), "r+", encoding="utf-8")
    file_type = open(join(TEST_DIRECTORY, NAME_FILE + FILE_TYPE).replace("\\", "/"), "r+", encoding="utf-8")

    program = file_refal.read()
    tips_program = file_type.read()

    lexer_refal = Lexer(program)
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
    file_type.close()

    if DEBUG_MODE:
        print(LINE_DELIMITER)

    parser_refal = ParserRefal(list_token_refal)
    parser_refal.parse()

    if DEBUG_MODE:
        print(LINE_DELIMITER)

    if DEBUG_MODE:
        print(parser_refal.ast)

    if DEBUG_MODE:
        print(LINE_DELIMITER)

    parser_refal_type = ParserRefalType(list_token_type)
    parser_refal_type.parse()

    if DEBUG_MODE:
        pass


except (FileNotFoundError, IOError) as e:
    sys.stderr.write(str(e))
    sys.exit(-1)


