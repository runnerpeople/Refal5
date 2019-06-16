#! python -v
# -*- coding: utf-8 -*-

from refal.tokens import *
from refal.ast import *
from refal.position import *

import sys


class ParserRefal(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.iteratorTokens = iter(self.tokens)
        self.cur_token = next(self.iteratorTokens)
        self.isError = False
        self.ast = None

    def get_variables(self, term):
        if isinstance(term, StructuralBrackets):
            variable = []
            for term in term.value:
                variable.extend(self.get_variables(term))
            return variable
        elif isinstance(term, CallBrackets):
            variable = []
            for term in term.content:
                variable.extend(self.get_variables(term))
            return variable
        elif isinstance(term, Variable):
            return [term.value]
        else:
            return []

    def check_call(self, term, ast_type):
        for term_content in term.content:
            if isinstance(term_content, CallBrackets):
                self.check_call(term_content, ast_type)

        has_body = False
        has_definition_type = False

        for function_new in self.ast.functions:
            if isinstance(function_new, Definition):
                if term.value == function_new.name:
                    has_body = True
                    break

        if not has_body:
            for function_definition_type in ast_type.functions:
                if isinstance(function_definition_type, DefinitionType):
                    if term.value == function_definition_type.name:
                        has_definition_type = True

        if not has_definition_type and not has_body:
            sys.stderr.write("Error. Unknown function %s\n" % term.value)
            self.isError = True

    def semantics_call(self, ast_type):
        if not self.isError:
            for function in self.ast.functions:
                if isinstance(function, Definition):
                    for sentence in function.sentences:
                        for term in sentence.result.terms:
                            if isinstance(term, CallBrackets):
                                self.check_call(term, ast_type)

    def semantics_variable(self, sentences):
        for sentence in sentences:
            variables = []
            for term in sentence.pattern.terms:
                variables.extend(self.get_variables(term))
            for condition in sentence.conditions:
                for term_condition in condition.pattern.terms:
                    variables.extend(self.get_variables(term_condition))
                for term_result in condition.result.terms:
                    out_variables = self.get_variables(term_result)
                    for variable in out_variables:
                        if variable not in variables:
                            sys.stderr.write(
                                "Error. Variable %s isn't found in previous sentence\n" % variable)
                            self.isError = True
            if sentence.block:
                self.semantics_variable(sentence.block)
            for term in sentence.result.terms:
                out_variables = self.get_variables(term)
                for variable in out_variables:
                    if variable not in variables:
                        sys.stderr.write("Error. Variable %s isn't found in previous sentence\n" % variable)
                        self.isError = True

    def semantics(self):
        names = set()
        for function in self.ast.functions:
            if function.name in names:
                sys.stderr.write("Error. Function %s already defined\n" % function.name)
                self.isError = True
            else:
                names.add(function.name)

        if not self.isError:
            for function in self.ast.functions:
                if isinstance(function, Definition):
                    for sentence in function.sentences:
                        for term in sentence.result.terms:
                            if isinstance(term, CallBrackets):
                                if term.value not in names:
                                    sys.stderr.write("Error. Function %s isn't defined\n" % term.value)
                                    self.isError = True
        # if not self.isError:
        #     for function in self.ast.functions:
        #         if isinstance(function, Definition):
        #             self.semantics_variable(function.sentences)

    def parse(self):
        self.ast = AST(self.parse_program())
        if self.cur_token.tag != DomainTag.Eop:
            self.isError = True
            sys.stderr.write("Error. Expected Token \"End_Of_Program\"\n")
        else:
            sys.stdout.write("Ok. Program satisfy grammar\n")

    # Program ::= Global*
    def parse_program(self):
        functions = self.parse_global()
        while self.cur_token.tag == DomainTag.Keyword or self.cur_token.tag == DomainTag.Ident or \
                (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
            functions.extend(self.parse_global())
        return functions

    # Global ::= Externs | Function | ';';
    def parse_global(self):
        if self.cur_token.tag == DomainTag.Keyword and self.cur_token.value == "$ENTRY" or \
                self.cur_token.tag == DomainTag.Ident:
            function = self.parse_function()
            return function
        elif self.cur_token.tag == DomainTag.Keyword:
            externs = self.parse_externs()
            return externs
        elif self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";":
            self.cur_token = next(self.iteratorTokens)
            return []

    # Externs ::= ExternKeyword 'Name' (',' 'Name')* ';';
    # ExternKeyword ::= '$EXTERN' | '$EXTRN' | '$EXTERNAL';
    def parse_externs(self):
        if self.cur_token.value == "$ENTRY":
            sys.stderr.write("Expected keyword: $EXTERN|$EXTRN|$EXTERNAL\n")
            self.isError = True
        else:
            self.cur_token = next(self.iteratorTokens)
            if self.cur_token.tag == DomainTag.Ident:
                externs = [Extern(self.cur_token.value, self.cur_token.coords)]
                self.cur_token = next(self.iteratorTokens)
                while self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ",":
                    self.cur_token = next(self.iteratorTokens)
                    if self.cur_token.tag != DomainTag.Ident:
                        sys.stderr.write("Expected name of external function\n")
                        self.isError = True
                        return []
                    else:
                        externs.append(Extern(self.cur_token.value, self.cur_token.coords))
                    self.cur_token = next(self.iteratorTokens)
                if not (self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";"):
                    sys.stderr.write("Expected \";\" after $EXTERNAL\n")
                    self.isError = True
                else:
                    self.cur_token = next(self.iteratorTokens)
                    return externs
            else:
                sys.stderr.write("Expected name of external function\n")
                self.isError = True
        return []

    # Function ::= ('$ENTRY')? 'Name' Body;
    def parse_function(self):
        is_entry = False
        if self.cur_token.tag == DomainTag.Keyword and self.cur_token.value == "$ENTRY":
            self.cur_token = next(self.iteratorTokens)
            is_entry = True
        if self.cur_token.tag != DomainTag.Ident:
            sys.stderr.write("Expected name of function\n")
            self.isError = True
            return []
        else:
            function_name = self.cur_token.value
            position = self.cur_token.coords
            self.cur_token = next(self.iteratorTokens)
            body = self.parse_body()
            return [Definition(function_name, position, is_entry, body)]

    # Body ::= '{' Sentences '}';
    def parse_body(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "{":
            self.cur_token = next(self.iteratorTokens)
            sentences = self.parse_sentences()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "}":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \"}\" after declaring function\n")
                self.isError = True
            return sentences
        else:
            sys.stderr.write("Expected \"{\" after declaring function\n")
            self.isError = True
            return []

    # Sentences ::= Sentence (';' Sentences?)?;
    def parse_sentences(self):
        sentence = self.parse_sentence()
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ";":
            self.cur_token = next(self.iteratorTokens)
            sentences = self.parse_sentences()
            sentence = [*sentence, *sentences]
            return sentence
        return sentence

    # Sentence ::= Pattern ( ('=' Result) | (',' Result ':' (Sentence | Body)) );
    def parse_sentence(self):
        starting_pos = self.cur_token.coords
        pattern = self.parse_pattern()
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "=":
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            following_pos = self.cur_token.coords
            return [Sentence(pattern, [], result, [], Fragment(starting_pos.starting, following_pos.following))]
        elif self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ",":
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result()
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ":":
                self.cur_token = next(self.iteratorTokens)
                if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "{":
                    body = self.parse_body()
                    following_pos = self.cur_token.coords
                    return [Sentence(pattern, [], result, body, Fragment(starting_pos.starting, following_pos.following))]
                else:
                    sentence = self.parse_sentence()[0]
                    following_pos = self.cur_token.coords
                    return [
                        Sentence(pattern, [*sentence.conditions, Condition(result, sentence.pattern)], sentence.result,
                                 sentence.block, Fragment(starting_pos.starting, following_pos.following))]
            else:
                sys.stderr.write("Expected \":\" after declaring result\n")
                self.isError = True
            return [Sentence(pattern, [], result, [])]
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
        return Expression(patternterm)

    # PatternTerm ::= Common | '(' Pattern ')';
    def parse_patternterm(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
            pattern = []
            self.cur_token = next(self.iteratorTokens)
            pattern.append(StructuralBrackets(self.parse_pattern().terms))
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                self.cur_token = next(self.iteratorTokens)
                return pattern
            else:
                sys.stderr.write("Expected \")\" after declaring pattern\n")
                self.isError = True
            return []
        else:
            return self.parse_common()

    # Common ::= 'Name' | ''chars'' | ""common"" | '123' | 'e.Var' | ε;
    def parse_common(self):
        if self.cur_token.tag == DomainTag.Ident:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [CompoundSymbol(token.value)]
        elif self.cur_token.tag == DomainTag.Characters:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [Char(token.value)]
        elif self.cur_token.tag == DomainTag.Number:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [Macrodigit(token.value)]
        elif self.cur_token.tag == DomainTag.Composite_symbol:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [CompoundSymbol(token.value)]
        elif self.cur_token.tag == DomainTag.Variable:
            token = self.cur_token
            self.cur_token = next(self.iteratorTokens)
            return [Variable(token.value, Type[token.value[0]], token.coords)]
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
        return Expression(resultterm)

    # ResultTerm ::= Common | '(' Result ')' | '<Name' Result '>';
    def parse_result_term(self):
        if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == "(":
            self.cur_token = next(self.iteratorTokens)
            result = [StructuralBrackets(self.parse_result().terms)]
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ")":
                self.cur_token = next(self.iteratorTokens)
                return result
            else:
                sys.stderr.write("Expected \")\" after declaring result\n")
                self.isError = True
            return []
        elif self.cur_token.tag == DomainTag.Left_bracket:
            func_name = self.cur_token.value[1:]
            pos = self.cur_token.coords
            self.cur_token = next(self.iteratorTokens)
            result = self.parse_result().terms
            if self.cur_token.tag == DomainTag.Mark_sign and self.cur_token.value == ">":
                self.cur_token = next(self.iteratorTokens)
            else:
                sys.stderr.write("Expected \">\" after declaring result\n")
                self.isError = True
            return [CallBrackets(func_name, pos, result)]
        else:
            return self.parse_common()


class ParserRefalType(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.iteratorTokens = iter(self.tokens)
        self.cur_token = next(self.iteratorTokens)
        self.isError = False
        self.ast = None

    def parse(self):
        self.ast = AST(self.parse_file(), True)
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
                or (self.cur_token.tag == DomainTag.Variable and (self.cur_token.value[0] == "s" or
                                                                  self.cur_token.value[0] == "t")) \
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
