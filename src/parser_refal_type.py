#! python -v
# -*- coding: utf-8 -*-

from src.tokens import *
from src.ast import *

import sys


class ParserRefalType(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.iteratorTokens = iter(self.tokens)
        self.cur_token = next(self.iteratorTokens)
        self.isError = False
        self.ast = None

    def parse(self):
        self.ast = AST(self.parse_file())
        if self.cur_token.tag != DomainTag.Eop:
            self.isError = True
            sys.stderr.write("Error. Expected Token \"End_Of_Program\"\n")
        else:
            sys.stdout.write("Ok. Program-Type satisfy grammar\n")

    def semantics(self):
        names = set()
        for function in self.ast.functions:
            if function.name in names:
                sys.stderr.write("Error. Function %s already defined\n" % function.name)
                self.isError = True
            else:
                names.add(function.name)

    # File ::= Function*
    def parse_file(self):
        function = self.parse_function()
        while self.cur_token.tag == DomainTag.Ident:
            function.extend(self.parse_function())
        return function

    # Function ::= 'Name' Format '=' Format ';'
    def parse_function(self):
        if self.cur_token.tag == DomainTag.Ident:
            func_name = self.cur_token.value
            pos = self.cur_token.coords
            self.cur_token = next(self.iteratorTokens)
            pattern = self.parse_format()
            result = []
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "=":
                self.cur_token = next(self.iteratorTokens)
                result = self.parse_format()
            else:
                sys.stderr.write("Expected \"=\" after declaring name of function\n")
                self.isError = True
            if not (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
                sys.stderr.write("Expected \";\" after function\n")
                self.isError = True
            else:
                self.cur_token = next(self.iteratorTokens)
                return [DefinitionType(func_name, pattern, result, pos)]
        return []

    # Format ::= Common ('e.Var' Common)?
    def parse_format(self):
        format_function = self.parse_common()
        if self.cur_token.tag == DomainTag.Variable and self.cur_token.value[0] == "e":
            format_function.append(Variable(self.cur_token.value, Type[self.cur_token.value[0]], self.cur_token.coords))
            self.cur_token = next(self.iteratorTokens)
            format_function.extend(self.parse_common())
        return Expression(format_function)

    # Common ::= ('Name' | ''chars'' | '123' | 's.Var' | 't.Var' | '(' Format ')')* | ε
    def parse_common(self):
        common_term = []
        while self.cur_token.tag == DomainTag.Ident or self.cur_token.tag == DomainTag.Number or \
                self.cur_token.tag == DomainTag.Characters or self.cur_token.tag == DomainTag.Composite_symbol \
                or (self.cur_token.tag == DomainTag.Variable and (self.cur_token.value[0] == "s" or self.cur_token.value[0] == "t")) \
                or (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "("):
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
                self.cur_token = next(self.iteratorTokens)
                common_term.append(StructuralBrackets(self.parse_format().terms))
                if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                    self.cur_token = next(self.iteratorTokens)
                else:
                    sys.stderr.write("Expected \")\" after declaring pattern\n")
                    self.isError = True
            else:
                if self.cur_token.tag == DomainTag.Ident:
                    token = self.cur_token
                    self.cur_token = next(self.iteratorTokens)
                    common_term.append(CompoundSymbol(token.value))
                elif self.cur_token.tag == DomainTag.Characters:
                    token = self.cur_token
                    self.cur_token = next(self.iteratorTokens)
                    common_term.append(Char(token.value))
                elif self.cur_token.tag == DomainTag.Number:
                    token = self.cur_token
                    self.cur_token = next(self.iteratorTokens)
                    common_term.append(Macrodigit(token.value))
                elif self.cur_token.tag == DomainTag.Composite_symbol:
                    token = self.cur_token
                    self.cur_token = next(self.iteratorTokens)
                    common_term.append(CompoundSymbol(token.value))
                elif self.cur_token.tag == DomainTag.Variable:
                    token = self.cur_token
                    self.cur_token = next(self.iteratorTokens)
                    common_term.append(Variable(token.value, Type[token.value[0]], token.coords))
        return common_term
