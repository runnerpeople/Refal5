#! python -v
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from enum import Enum

from refal.constants import *


class AST(object):

    def __init__(self, functions, is_file_type=False, default_functions=None):

        if not is_file_type:
            # Для доступности default-функций:
            if default_functions is None:
                default_functions = [Extern(name) for name in DEFAULT_FUNCTIONS]
            # default_functions = []
            self.functions = [*default_functions, *functions]
        else:
            self.functions = functions

    def __str__(self):
        return str("\n".join(list(map(str, self.functions))))

    def clone(self):
        return AST([function.clone() for function in self.functions if isinstance(function, Definition)], False, [])


class Function(ABC):

    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __eq__(self, other):
        return isinstance(other, Function) and self.name == other.name

    @abstractmethod
    def __str__(self):
        return self.name

    @abstractmethod
    def clone(self):
        raise NotImplementedError("Can't clone abstract class")


class Extern(Function):

    def __init__(self, name, pos=None):
        super(Extern, self).__init__(name, pos)

    def __eq__(self, other):
        return isinstance(other, Extern) and self.name == other.name

    def __str__(self):
        return "$EXTERN " + self.name

    def clone(self):
        return Extern(self.name, self.pos.clone())


class Definition(Function):

    def __init__(self, name, pos, is_entry=False, sentences=None):
        super(Definition, self).__init__(name, pos)
        if sentences is None:
            sentences = []
        self.is_entry = is_entry
        self.sentences = sentences

    def __eq__(self, other):
        return isinstance(other, Definition) and self.name == other.name

    def __str__(self):
        return self.name + " {\n" + ";\n".join(list(map(str, self.sentences))) + ";\n}"

    def clone(self):
        return Definition(self.name, self.pos.clone(), self.is_entry,
                          [sentences.clone() for sentences in self.sentences])


class DefinitionType(Function):

    def __init__(self, name, pattern, result, pos):
        super(DefinitionType, self).__init__(name, pos)
        self.pattern = pattern
        self.result = result

    def __eq__(self, other):
        return isinstance(other, DefinitionType) and self.name == other.name

    def __str__(self):
        return self.name + " " + str(self.pattern) + " = " + str(self.result)

    def clone(self):
        return DefinitionType(self.name, self.pattern.clone(), self.result.clone(), self.pos.clone())


class Sentence(object):

    def __init__(self, pattern, conditions, result, block, pos=None):
        self.pattern = pattern
        self.conditions = conditions
        self.result = result
        self.block = block

        self.pos = pos

        self.has_call = False
        self.no_substitution = False

    def __eq__(self, other):
        return isinstance(other, Sentence) \
               and self.pattern == other.pattern \
               and self.conditions == other.conditions \
               and self.result == other.result \
               and self.block == other.block

    def __str__(self):
        result_str = "\t" + str(self.pattern)
        if self.conditions:
            result_str += (", " + ",\t".join(list(map(str, self.conditions[::-1]))))
        if self.block:
            result_str += (", " + str(self.result))
        if self.block:
            result_str += (" :\n\t{\n\t\t" + ";\n\t\t".join(list(map(str, self.block))) + ";\n\t}")
        if self.result is not None and not self.block:
            result_str += (" = " + str(self.result))
        return result_str

    def clone(self):
        sentence_copy = Sentence(self.pattern.clone(), [condition.clone() for condition in self.conditions],
                                 self.result.clone(),
                                 [block.clone() for block in self.block], self.pos.clone())
        sentence_copy.has_call = self.has_call
        sentence_copy.no_substitution = self.no_substitution
        return sentence_copy


class Condition(object):

    def __init__(self, result, pattern):
        self.result = result
        self.pattern = pattern

    def __str__(self):
        return str(self.result) + " : " + str(self.pattern)

    def clone(self):
        return Condition(self.result.clone(), self.pattern.clone())


class Expression(object):

    def __init__(self, terms):
        self.terms = terms

    def __eq__(self, other):
        return isinstance(other, Expression) and self.terms == other.terms

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return " ".join(list(map(str, self.terms)))

    def clone(self):
        return Expression([term.clone() for term in self.terms])


class Term(ABC):

    def __init__(self, value):
        self.value = value

    @abstractmethod
    def __str__(self):
        return str(self.value)

    @abstractmethod
    def clone(self):
        raise NotImplementedError("Can't clone abstract class")


class Char(Term):

    def __init__(self, value):
        super(Char, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, Char) and self.value == other.value

    def __str__(self):
        return super(Char, self).__str__()

    def clone(self):
        return Char(self.value)


class Macrodigit(Term):

    def __init__(self, value):
        super(Macrodigit, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, Macrodigit) and self.value == other.value

    def __str__(self):
        return super(Macrodigit, self).__str__()

    def clone(self):
        return Macrodigit(self.value)


class CompoundSymbol(Term):

    def __init__(self, value):
        super(CompoundSymbol, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, CompoundSymbol) and self.value == other.value

    def __str__(self):
        return super(CompoundSymbol, self).__str__()

    def clone(self):
        return CompoundSymbol(self.value)


class StructuralBrackets(Term):

    def __init__(self, value):
        super(StructuralBrackets, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, StructuralBrackets) and self.value == other.value

    def __str__(self):
        return "(" + " ".join(list(map(str, self.value))) + ")"

    def clone(self):
        return StructuralBrackets([value.clone() for value in self.value])


class CallBrackets(Term):

    def __init__(self, func_name, pos, content):
        super(CallBrackets, self).__init__(func_name)
        self.pos = pos
        self.content = content

    def __str__(self):
        return "<" + self.value + " " + " ".join(list(map(str, self.content))) + ">"

    def clone(self):
        return CallBrackets(self.value, self.pos.clone(), [content.clone() for content in self.content])


class Type(Enum):
    s = 1
    t = 2
    e = 3


class Variable(Term):

    def __init__(self, value, type_variable, pos, index=-1, sentence_index=-1):
        super(Variable, self).__init__(value)
        self.type_variable = type_variable
        self.index = index
        self.pos = pos
        self.sentence_index = sentence_index

    def __eq__(self, other):
        return isinstance(other, Variable) and self.type_variable == other.type_variable and self.index == other.index

    def __str__(self):
        if self.type_variable == Type.s:
            return "s." + str(self.index)
        elif self.type_variable == Type.t:
            return "t." + str(self.index)
        elif self.type_variable == Type.e:
            return "e." + str(self.index)

    def clone(self):
        return Variable(self.value, self.type_variable, None if self.pos is None else self.pos.clone(), self.index, self.sentence_index)
