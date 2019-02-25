#! python -v
# -*- coding: utf-8 -*-

from src.tokens import *

import sys


def print_sentence(dict_function):
    for key in dict_function.keys():
        values = dict_function[key]
        for value in values:
            pattern = ", ".join(value[0])
            term = ", ".join(value[1])
            if not pattern:
                pattern = "/* пусто */"
            if not term:
                term = "/* пусто */"
            print(key, ":" , pattern, "->", term)


def diff(first, second):
    second = set(second)
    return [item for item in first if item not in second]


class ParserRefal(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.iteratorTokens = iter(self.tokens)
        self.cur_token = next(self.iteratorTokens)
        self.isError = False
        self.available_functions = ["Add", "Sub", "Mul", "Div", "Mod", "Residue"]
        self.call_functions = []
        self.sentences = dict()

        self.__depth = 0

    def parse(self):
        self.parse_program()
        if self.cur_token.tag != DomainTag.Eop:
            self.isError = True
            sys.stderr.write("Error. Expected Token \"End_Of_Program\"\n")
        elif len(diff(self.call_functions, self.available_functions)) == 0:
            self.isError = True
            sys.stderr.write("Error. Some function aren't defined")
        else:
            sys.stdout.write("Ok. Program satisfy grammar\n")

    # Program ::= Global*
    def parse_program(self):
        self.parse_global()
        while self.cur_token.tag == DomainTag.Keyword or self.cur_token.tag == DomainTag.Ident or \
                (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
            self.parse_global()

    # Global ::= Externs | Function | ';';
    def parse_global(self):
        if self.cur_token.tag == DomainTag.Keyword and self.cur_token.value == "$ENTRY" or \
                self.cur_token.tag == DomainTag.Ident:
            self.parse_function()
        elif self.cur_token.tag == DomainTag.Keyword:
            self.parse_externs()
        elif self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";":
            self.cur_token = next(self.iteratorTokens)

    # Externs ::= ExternKeyword 'Name' (',' 'Name')* ';';
    # ExternKeyword ::= '$EXTERN' | '$EXTRN' | '$EXTERNAL';
    def parse_externs(self):
        if self.cur_token.value == "$ENTRY":
            sys.stderr.write("Expected keyword: $EXTERN|$EXTRN|$EXTERNAL\n")
        else:
            self.cur_token = next(self.iteratorTokens)
            if self.cur_token.tag == DomainTag.Ident:
                if self.cur_token.value not in self.available_functions:
                    self.available_functions.append(self.cur_token.value)
                else:
                    self.isError = True
                    sys.stderr.write("Error. Function %s are redefined" % self.cur_token.value)
                self.cur_token = next(self.iteratorTokens)
                while self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ",":
                    self.cur_token = next(self.iteratorTokens)
                    if self.cur_token.tag != DomainTag.Ident:
                        sys.stderr.write("Expected name of external function\n")
                    else:
                        self.available_functions.append(self.cur_token.value)
                    self.cur_token = next(self.iteratorTokens)
                if not (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
                    sys.stderr.write("Expected \";\" after $EXTERNAL\n")
                else:
                    self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected name of external function\n")

    # Function ::= ('$ENTRY')? 'Name' Body;
    def parse_function(self):
        if self.cur_token.tag == DomainTag.Keyword and self.cur_token.value == "$ENTRY":
            self.cur_token = next(self.iteratorTokens)
        if self.cur_token.tag != DomainTag.Ident:
            sys.stderr.write("Expected name of function\n")
        else:
            function_name = self.cur_token.value
            if self.cur_token.value in self.available_functions:
                self.isError = True
                sys.stderr.write("Error. Function %s is redefined" % self.cur_token.value)
            else:
                self.available_functions.append(self.cur_token.value)
            self.cur_token = next(self.iteratorTokens)
            self.sentences[function_name] = self.parse_body()

    # Body ::= '{' Sentences '}';
    def parse_body(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "{":
            self.cur_token = next(self.iteratorTokens)
            self.__depth = 0
            sentences = self.parse_sentences()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "}":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \"}\" after declaring function\n")
            return sentences
        else:
            sys.stderr.write("Expected \"{\" after declaring function\n")

    # Sentences ::= Sentence (';' Sentences?)?;
    def parse_sentences(self):
        sentence = self.parse_sentence()
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";":
            self.cur_token = next(self.iteratorTokens)
            sentences = self.parse_sentences()
            if sentences == []:
                return sentence
            else:
                self.__depth += 1
            if self.__depth >= 2:
                sentence = [sentence,*sentences]
            else:
                sentence = [sentence,sentences]
            return sentence
        return sentence

    # Sentence ::= Pattern ( ('=' Result) | (',' Result ':' (Sentence | Body)) );
    def parse_sentence(self):
        pattern = self.parse_pattern()
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "=":
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            return [pattern, result]
        elif self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ",":
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ":":
                self.cur_token = next(self.iteratorTokens)
                if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "{":
                    sentences = self.parse_body()
                    return [pattern, result].append(sentences)
                else:
                    sentence = self.parse_sentence()
                    return [pattern, result].append(sentence)
            else:
                sys.stderr.write("Expected \":\" after declaring result\n")
            return [pattern, result]
        return []
        # else:
        #     sys.stderr.write("Expected \"=\" or \",\" after declaring pattern\n")

    # Pattern ::= PatternTerm*;
    def parse_pattern(self):
        patternterm = self.parse_patternterm()
        while self.cur_token.tag == DomainTag.Ident or self.cur_token.tag == DomainTag.Number or \
                self.cur_token.tag == DomainTag.Characters or self.cur_token.tag == DomainTag.Composite_symbol \
                or self.cur_token.tag == DomainTag.Variable \
                or (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "("):
            patternterm.extend(self.parse_patternterm())
        return patternterm

    # PatternTerm ::= Common | '(' Pattern ')';
    def parse_patternterm(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
            self.cur_token = next(self.iteratorTokens)
            pattern = self.parse_pattern()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \")\" after declaring pattern\n")
            return pattern
        else:
            return self.parse_common()

    # Common ::= 'Name' | ''chars'' | ""common"" | '123' | 'e.Var' | ε;
    def parse_common(self):
        if self.cur_token.tag == DomainTag.Ident:
            self.cur_token = next(self.iteratorTokens)
            return []
        elif self.cur_token.tag == DomainTag.Characters:
            self.cur_token = next(self.iteratorTokens)
            return []
        elif self.cur_token.tag == DomainTag.Number:
            self.cur_token = next(self.iteratorTokens)
            return []
        elif self.cur_token.tag == DomainTag.Composite_symbol:
            self.cur_token = next(self.iteratorTokens)
            return []
        elif self.cur_token.tag == DomainTag.Variable:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [token.value]
        else:
            return []

    # Result ::= ResultTerm*;
    def parse_result(self):
        resultterm = self.parse_result_term()
        while self.cur_token.tag == DomainTag.Ident or self.cur_token.tag == DomainTag.Number or \
                self.cur_token.tag == DomainTag.Characters or self.cur_token.tag == DomainTag.Composite_symbol \
                or self.cur_token.tag == DomainTag.Variable \
                or (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(") \
                or (self.cur_token.tag == DomainTag.Left_bracket):
            resultterm.extend(self.parse_result_term())
        return resultterm

    # ResultTerm ::= Common | '(' Result ')' | '<Name' Result '>';
    def parse_result_term(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \")\" after declaring result\n")
            return result
        elif self.cur_token.tag == DomainTag.Left_bracket:
            if self.cur_token.value[1:] not in self.call_functions:
                self.call_functions.append(self.cur_token.value[1:])
            elif self.cur_token.value[1:] not in self.available_functions:
                self.isError = True
                sys.stderr.write("Error. Function %s aren't defined" % self.cur_token.value[1:])
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ">":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \">\" after declaring result\n")
            return result
        else:
            return self.parse_common()
