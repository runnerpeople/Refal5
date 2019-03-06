#! python -v
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from enum import Enum


class DomainTag(Enum):
    Keyword = 1
    Ident = 2
    Number = 3
    Variable = 4
    Composite_symbol = 5
    Characters = 6
    Mark_sign = 7
    Left_bracket = 8
    Eop = 9
    Unknown = 10


class Token(ABC):

    def __init__(self, tag, coords, value):
        self.tag = tag
        self.coords = coords
        self.value = value

    def __eq__(self, other):
        return self.tag == other.tag and self.value == other.value

    @abstractmethod
    def __str__(self):
        return str(self.coords)


class KeywordToken(Token):

    def __init__(self, value, coords=None):
        super(KeywordToken, self).__init__(DomainTag.Keyword, coords, value)

    def __str__(self):
        return "Extern " + super(KeywordToken, self).__str__() + ": " + self.value


class IdentToken(Token):

    def __init__(self, value, coords=None):
        super(IdentToken, self).__init__(DomainTag.Ident, coords, value)

    def __str__(self):
        return "Ident " + super(IdentToken, self).__str__() + ": " + self.value


class VariableToken(Token):

    def __init__(self, value, coords=None):
        super(VariableToken, self).__init__(DomainTag.Variable, coords, value)

    def __str__(self):
        return "Variable " + super(VariableToken, self).__str__() + ": " + self.value


class CompositeSymbolToken(Token):

    def __init__(self, value, coords=None):
        super(CompositeSymbolToken, self).__init__(DomainTag.Composite_symbol, coords, value)

    def __str__(self):
        return "CompositeSymbol " + super(CompositeSymbolToken, self).__str__() + ": " + self.value


class CharacterToken(Token):

    def __init__(self, value, coords=None):
        super(CharacterToken, self).__init__(DomainTag.Characters, coords, value)

    def __str__(self):
        return "Characters " + super(CharacterToken, self).__str__() + ": " + self.value


class MarkSignToken(Token):

    def __init__(self, value, coords=None):
        super(MarkSignToken, self).__init__(DomainTag.Mark_sign, coords, value)

    def __str__(self):
        return "Sign " + super(MarkSignToken, self).__str__() + ": " + self.value


class LeftBracketToken(Token):
    def __init__(self, value, coords=None):
        super(LeftBracketToken, self).__init__(DomainTag.Left_bracket, coords, value)

    def __str__(self):
        return "Left Bracket: " + super(LeftBracketToken, self).__str__() + ": " + self.value


class NumberToken(Token):

    def __init__(self, value, coords=None):
        super(NumberToken, self).__init__(DomainTag.Number, coords, value)

    def __str__(self):
        return "Number " + super(NumberToken, self).__str__() + ": " + str(self.value)


class UnknownToken(Token):

    def __init__(self, value, coords=None):
        super(UnknownToken, self).__init__(DomainTag.Unknown, coords, value)

    def __str__(self):
        return super(UnknownToken, self).__str__() + "= " + self.value


class EopToken(Token):

    def __init__(self, coords=None):
        super(EopToken, self).__init__(DomainTag.Eop, coords, "")

    def __str__(self):
        return ""
