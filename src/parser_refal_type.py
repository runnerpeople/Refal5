#! python -v
# -*- coding: utf-8 -*-

from src.tokens import *

import sys


class ParserRefalType(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.iteratorTokens = iter(self.tokens)
        self.cur_token = next(self.iteratorTokens)
        self.isError = False
        self.available_functions = ["Add", "Sub", "Mul", "Div", "Mod", "Residue"]

    def parse(self):
        self.parse_file()
        if self.cur_token.tag != DomainTag.Eop:
            self.isError = True
            sys.stderr.write("Error. Expected Token \"End_Of_Program\"\n")
        else:
            sys.stdout.write("Ok. Program satisfy grammar\n")

    # File ::= Function*
    def parse_file(self):
        self.parse_function()
        while self.cur_token.tag == DomainTag.Ident:
            self.parse_function()

    # Function ::= 'Name' Format '=' Format ';'
    def parse_function(self):
        if self.cur_token.tag == DomainTag.Ident:
            self.available_functions.append(self.cur_token.value)
            self.cur_token = next(self.iteratorTokens)
            self.parse_format()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "=":
                self.cur_token = next(self.iteratorTokens)
                self.parse_format()
            else:
                sys.stderr.write("Expected \"=\" after declaring name of function\n")
            if not (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
                sys.stderr.write("Expected \";\" after function\n")
            else:
                self.cur_token = next(self.iteratorTokens)

    # Format ::= Common ('e.Var' Common)?
    def parse_format(self):
        self.parse_common()
        if self.cur_token.tag == DomainTag.Variable:
            self.cur_token = next(self.iteratorTokens)
            self.parse_common()

    # Common ::= 'Name' | ''chars'' | '123' | 'e.Var' | ('(' Format ')')* | ε
    def parse_common(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
            self.cur_token = next(self.iteratorTokens)
            self.parse_format()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \")\" after declaring pattern\n")
        else:
            if self.cur_token.tag == DomainTag.Ident:
                self.cur_token = next(self.iteratorTokens)
            elif self.cur_token.tag == DomainTag.Characters:
                self.cur_token = next(self.iteratorTokens)
            elif self.cur_token.tag == DomainTag.Number:
                self.cur_token = next(self.iteratorTokens)
            elif self.cur_token.tag == DomainTag.Composite_symbol:
                self.cur_token = next(self.iteratorTokens)
            elif self.cur_token.tag == DomainTag.Variable:
                self.cur_token = next(self.iteratorTokens)
