#! python -v
# -*- coding: utf-8 -*-

from refal.position import *
from refal.tokens import *
from refal.constants import *

from copy import deepcopy
import sys


def next_or_current(obj):
    return next(deepcopy(obj), obj)


def refactor_char_token(tokens):
    i = 0
    while i < len(tokens):
        if isinstance(tokens[i], CharacterToken):
            if len(tokens[i].value) > 3:
                new_tokens = []
                ch = ""
                position = deepcopy(tokens[i].coords)
                for j in range(len(tokens[i].value)):
                    if tokens[i].value[j] == "'" and ch == "":
                        continue
                    if ch == "\\" and tokens[i].value[j] != "\\":
                        ch += tokens[i].value[j]
                        ch = "'" + ch + "'"
                        new_tokens.append(CharacterToken(ch, position))
                        ch = ""
                    elif tokens[i].value[j] == "\\":
                        ch += tokens[i].value[j]
                    else:
                        ch += tokens[i].value[j]
                        ch = "'" + ch + "'"
                        new_tokens.append(CharacterToken(ch, position))
                        ch = ""
                if len(new_tokens) > 1:
                    tokens = tokens[:i] + new_tokens + tokens[i+1:]
                    i = -1
        i += 1
    return tokens


class Lexer(object):

    def __init__(self, program):
        self.program = program
        self.cur = Position(program)

    def read_keyword(self):
        new_pos = next_or_current(self.cur)
        s = "$"
        if new_pos.letter() == "E":
            s += new_pos.letter()
            new_pos = next_or_current(new_pos)
            if new_pos.letter() == "N" or new_pos.letter() == "X":
                s += new_pos.letter()
                new_pos = next_or_current(new_pos)
                if new_pos.letter() == "T":
                    s += new_pos.letter()
                    new_pos = next_or_current(new_pos)
                    if new_pos.letter() == "E" and s[-2] != "N" or new_pos.letter() == "R":
                        s += new_pos.letter()
                        new_pos = next_or_current(new_pos)
                        if new_pos.letter() == "N" and s[-1] != "E" or new_pos.letter() == "R" \
                                or new_pos.letter() == "Y" and s[2] == "N":
                            s += new_pos.letter()
                            if s == "$EXTRN" or s == "$ENTRY":
                                return KeywordToken(s, Fragment(self.cur, new_pos))
                            new_pos = next_or_current(new_pos)
                            if new_pos.letter() == "N":
                                s += new_pos.letter()
                                new_pos = next_or_current(new_pos)
                                if new_pos.letter() == "A":
                                    s += new_pos.letter()
                                    new_pos = next_or_current(new_pos)
                                    if new_pos.letter() == "L":
                                        s += new_pos.letter()
                                        new_pos = next_or_current(new_pos)
                                        if not new_pos.is_letter():
                                            return KeywordToken(s, Fragment(self.cur, new_pos))
                                elif new_pos != next_or_current(new_pos) and not new_pos.is_letter():
                                    return KeywordToken(s, Fragment(self.cur, new_pos))
        else:
            return UnknownToken("$", Fragment(self.cur, self.cur))
        return UnknownToken("$", Fragment(self.cur, self.cur))

    def read_macro_number(self):
        new_pos = next_or_current(self.cur)
        s = self.cur.letter()
        if new_pos != next_or_current(new_pos) and (new_pos.is_decimal_digit()):
            s += new_pos.letter()
            while new_pos != next_or_current(new_pos) and next_or_current(new_pos).is_decimal_digit():
                new_pos = next_or_current(new_pos)
                s += new_pos.letter()
            return NumberToken(int(s), Fragment(self.cur, new_pos))

        return NumberToken(int(s), Fragment(self.cur, self.cur))

    def read_ident_or_variable(self):
        new_pos = next_or_current(self.cur)
        s = self.cur.letter()
        if new_pos.letter() == "." and s in ["s", "t", "e"]:
            s += new_pos.letter()
            new_pos = next_or_current(new_pos)
            if new_pos.is_decimal_digit():
                s += new_pos.letter()
                while new_pos != next_or_current(new_pos) and next_or_current(new_pos).is_decimal_digit():
                    new_pos = next_or_current(new_pos)
                    s += new_pos.letter()
                return VariableToken(s, Fragment(self.cur, new_pos))
            elif new_pos.is_latin_letter():
                s += new_pos.letter()
                while new_pos != next_or_current(new_pos) and (next_or_current(new_pos).is_letter_or_digit() or
                                                               next_or_current(new_pos).letter() in ["-", "_"]):
                    new_pos = next_or_current(new_pos)
                    s += new_pos.letter()
                return VariableToken(s, Fragment(self.cur, new_pos))
            else:
                return UnknownToken(s, Fragment(self.cur, new_pos))
        elif new_pos.letter() == ".":
            return IdentToken(s, Fragment(self.cur, next(self.cur, self.cur)))
        if new_pos != next_or_current(new_pos) and (new_pos.is_letter_or_digit() or new_pos.letter() in ["-", "_"]):
            s += new_pos.letter()
            # new_pos = next(copy.deepcopy(new_pos),  new_pos)
            while new_pos != next_or_current(new_pos) and (next_or_current(new_pos).is_letter_or_digit() or
                                                           next_or_current(new_pos).letter() in ["-", "_"]):
                new_pos = next_or_current(new_pos)
                s += new_pos.letter()
            return IdentToken(s, Fragment(self.cur, new_pos))
        return IdentToken(s, Fragment(self.cur, new_pos))

    def read_symbol(self):
        new_pos = next_or_current(self.cur)
        s = self.cur.letter()
        while new_pos != next_or_current(new_pos) and new_pos.letter() != "\"":
            if new_pos.letter() == "\\":
                s += new_pos.letter()
                new_pos = next_or_current(new_pos)
                if new_pos.letter() in ["\\", "n", "r", "t", "\"", "\'", "(", ")", "<", ">"]:
                    s += new_pos.letter()
                    new_pos = next_or_current(new_pos)
                elif new_pos.letter() == "x":
                    s += new_pos.letter()
                    new_pos = next_or_current(new_pos)
                    if new_pos != next_or_current(new_pos):
                        for _ in range(0, 2):
                            if new_pos.is_decimal_digit() or ("a" <= new_pos.letter() <= "f" or
                                                              "A" <= new_pos.letter() <= "F"):
                                s += new_pos.letter()
                                new_pos = next_or_current(new_pos)
                            else:
                                return UnknownToken(s, Fragment(self.cur, new_pos))
                        return CompositeSymbolToken(s, Fragment(self.cur, new_pos))
                else:
                    return UnknownToken(s, Fragment(self.cur, new_pos))
            else:
                s += new_pos.letter()
                new_pos = next_or_current(new_pos)
        if new_pos != next_or_current(new_pos):
            s += new_pos.letter()
            return CompositeSymbolToken(s, Fragment(self.cur, new_pos))
        else:
            return UnknownToken(s, Fragment(self.cur, new_pos))

    def read_chars(self):
        new_pos = next_or_current(self.cur)
        s = self.cur.letter()
        while new_pos != next_or_current(new_pos) and new_pos.letter() != "\'":
            if new_pos.letter() == "\\":
                s += new_pos.letter()
                new_pos = next_or_current(new_pos)
                if new_pos.letter() in ["\\", "n", "r", "t", "\"", "\'", "(", ")", "<", ">"]:
                    s += new_pos.letter()
                    new_pos = next_or_current(new_pos)
                elif new_pos.letter() == "x":
                    s += new_pos.letter()
                    new_pos = next_or_current(new_pos)
                    if new_pos != next_or_current(new_pos):
                        for _ in range(0, 2):
                            if new_pos.is_decimal_digit() or ("a" <= new_pos.letter() <= "f" or
                                                              "A" <= new_pos.letter() <= "F"):
                                s += new_pos.letter()
                                new_pos = next_or_current(new_pos)
                            else:
                                return UnknownToken(s, Fragment(self.cur, new_pos))
                        return CharacterToken(s, Fragment(self.cur, new_pos))
                else:
                    return UnknownToken(s, Fragment(self.cur, new_pos))
            else:
                s += new_pos.letter()
                new_pos = next_or_current(new_pos)
        if new_pos != next_or_current(new_pos):
            s += new_pos.letter()
            return CharacterToken(s, Fragment(self.cur, new_pos))
        else:
            return UnknownToken(s, Fragment(self.cur, new_pos))

    def read_left_call_or_mark(self):
        new_pos = next_or_current(self.cur)
        s = self.cur.letter()
        if new_pos != next_or_current(new_pos) and new_pos.letter() in ["+", "-", "*", "/", "%", "?"]:
            s += new_pos.letter()
            return LeftBracketToken(s, Fragment(self.cur, new_pos))
        while new_pos.is_white_space():
            new_pos = next_or_current(new_pos)
        if new_pos != next_or_current(new_pos):
            s += new_pos.letter()
            while new_pos != next_or_current(new_pos) and (next_or_current(new_pos).is_letter_or_digit() or
                                                           next_or_current(new_pos).letter() in ["-", "_"]):
                new_pos = next_or_current(new_pos)
                s += new_pos.letter()
            return LeftBracketToken(s, Fragment(self.cur, new_pos))
        else:
            return UnknownToken(s, Fragment(self.cur, new_pos))

    def read_many_line_comment(self):
        s = self.cur.letter()
        new_pos = next_or_current(self.cur)
        s += new_pos.letter()
        new_pos = next(new_pos, new_pos)
        while new_pos != next_or_current(new_pos) and not (new_pos.letter() == "*" and
                                                           next_or_current(new_pos).letter() == "/"):
            s += new_pos.letter()
            new_pos = next_or_current(new_pos)
        s += new_pos.letter()
        new_pos = next(new_pos, new_pos)
        s += new_pos.letter()
        if DEBUG_MODE:
            sys.stdout.write("Recognize many-line comment[" + str(Fragment(self.cur, new_pos)) + "]: " + s + "\n")
        new_pos = next_or_current(new_pos)
        self.cur = new_pos

    def read_comment(self):
        new_pos = next_or_current(self.cur)
        s = "*"
        while new_pos != next_or_current(new_pos) and not (new_pos.letter() == "\n"):
            s += new_pos.letter()
            new_pos = next_or_current(new_pos)
        new_pos = next_or_current(new_pos)
        if DEBUG_MODE:
            sys.stdout.write("Recognize one-line comment[" + str(Fragment(self.cur, new_pos)) + "]: " + s + "\n")
        self.cur = new_pos

    def next_token(self):
        tok = UnknownToken(self.cur.letter(), Fragment(self.cur, self.cur))
        while tok.tag == DomainTag.Unknown:
            while self.cur.is_white_space():
                self.cur = next(self.cur, self.cur)
            if self.cur.letter() == "/" and self.cur != next_or_current(self.cur) and \
                    next_or_current(self.cur).letter() == "*":
                self.read_many_line_comment()
                continue
            if self.cur.letter() == "*":
                self.read_comment()
                continue
            if self.cur.is_eof():
                tok = EopToken(Fragment(self.cur, self.cur))
            else:
                if self.cur.letter() == "$":
                    read_tok = self.read_keyword()
                elif self.cur.letter() == "\"":
                    read_tok = self.read_symbol()
                elif self.cur.letter() == "\'":
                    read_tok = self.read_chars()
                elif self.cur.letter() == "<":
                    read_tok = self.read_left_call_or_mark()
                elif self.cur.letter() in ['[', '(', ')', '>', '=', ';', ':', ',', '{', '}', ']']:
                    read_tok = MarkSignToken(self.cur.letter(), Fragment(self.cur, self.cur))
                elif self.cur.is_decimal_digit():
                    read_tok = self.read_macro_number()
                elif self.cur.is_latin_letter():
                    read_tok = self.read_ident_or_variable()
                else:
                    read_tok = UnknownToken(self.cur.letter(), Fragment(self.cur, self.cur))
                if read_tok.tag == DomainTag.Unknown:
                    sys.stderr.write("Token[" + str(read_tok) + "]: unrecognized token\n")
                    self.cur = next(self.cur, self.cur)
                else:
                    self.cur = read_tok.coords.following
                    self.cur = next_or_current(self.cur)
                    tok = read_tok
        return tok
