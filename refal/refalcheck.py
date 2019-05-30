#! python -v
# -*- coding: utf-8 -*-

from refal.lexer_refal import *
from refal.parser_refal import *
from refal.algorithm import *
from refal.constants import *

import sys
import argparse


def get_file_name(file_path):
    head, tail = split(file_path)
    return tail


def new_parser():
    parser = argparse.ArgumentParser(description="Arguments for program refalcheck")
    parser.add_argument("file", help="File for which format functions is calculated")
    parser.add_argument("file_type", nargs="*", help="Files, contained required format functions")
    return parser


def calculate_ast(file_path, is_file_type=False):
    try:
        file_refal = open(file_path, "r+", encoding="utf-8")
    except (FileNotFoundError, IOError) as e:
        sys.stderr.write(str(e))
        sys.exit(-1)

    if DEBUG_MODE:
        print("Lexer %s" % get_file_name(file_path))

    program = file_refal.read()
    lexer = Lexer(program)

    cur_token = lexer.next_token()
    list_token = [cur_token]

    if DEBUG_MODE:
        print(cur_token)
    while cur_token.tag != DomainTag.Eop:
        cur_token = lexer.next_token()
        if DEBUG_MODE:
            print(cur_token)
        list_token.append(cur_token)

    list_token = refactor_char_token(list_token)

    file_refal.close()

    if DEBUG_MODE:
        print(LINE_DELIMITER)

    if DEBUG_MODE:
        print("Parser %s" % get_file_name(file_path))

    if not is_file_type:
        parser = ParserRefal(list_token)
    else:
        parser = ParserRefalType(list_token)
    parser.parse()

    parser.semantics()

    if DEBUG_MODE:
        print(LINE_DELIMITER)

    return parser


def append_ast(parser_left, parser_right):
    if not parser_left.isError and not parser_right.isError:
        parser_left.ast.functions.extend(parser_right.ast.functions)
        return parser_left
    else:
        sys.stderr.write("Can't append AST, because it was error")


def main():
    arg_parse = new_parser()
    args = arg_parse.parse_args()

    file_refal_path = None
    if DEBUG_MODE:
        file_refal_path = join(TEST_DIRECTORY, args.file).replace("\\", "/")
    else:
        file_refal_path = args.file

    parser_refal = calculate_ast(file_refal_path)

    file_type_path = "built-in.type"
    parser_refal_type = calculate_ast(file_type_path, True)

    for file in args.file_type:
        if DEBUG_MODE:
            file_refal_path = join(TEST_DIRECTORY, file).replace("\\", "/")
        else:
            file_refal_path = file

        append_ast(parser_refal_type, calculate_ast(file_refal_path, True))

    parser_refal.semantics_call(parser_refal_type.ast)

    if not parser_refal.isError and not parser_refal_type.isError:
        calculation = Calculation(parser_refal.ast, parser_refal_type.ast)
        calculation.calculate_system()
        print(calculation.print_format_function())


if __name__ == "__main__":
    main()
