#! python -v
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from enum import Enum

DEFAULT_FUNCTIONS = ["Mu", "Add", "Arg", "Br", "Card", "Chr", "Cp", "Dg", "Dgall", "Div", "Divmod",
                     "Explode", "First", "Get", "Implode", "Last", "Lenw", "Lower", "Mod", "Mul",
                     "Numb", "Open", "Ord", "Print", "Prout", "Put", "Putout", "Rp", "Step",
                     "Sub", "Symb", "Time", "Type", "Upper", "Freeze", "Dn",
                     "Up", "Ev-met", "Residue", "System", "Exit", "Close", "ExistFile", "GetCurrentDirectory",
                     "RemoveFile", "SizeOf", "GetPID", "GetPPID",
                     "Implode_Ext", "Explode_Ext", "TimeElapsed", "Compare", "Random", "RandomDigit", "Write", "ListOfBuiltin",
                     "Sysfun", "DeSysfun", "XMLParse", "GetEnv"]


class AST(object):

    def __init__(self, functions):

        # Для доступности default-функций:
        default_functions = [Extern(name) for name in DEFAULT_FUNCTIONS]
        self.functions = [*default_functions, *functions]

    def __str__(self):
        return str("\n".join(list(map(str, self.functions))))


class Function(ABC):

    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __eq__(self, other):
        return isinstance(other, Function) and self.name == other.name

    @abstractmethod
    def __str__(self):
        return self.name


class Extern(Function):

    def __init__(self, name, pos=None):
        super(Extern, self).__init__(name, pos)

    def __eq__(self, other):
        return isinstance(other, Extern) and self.name == other.name

    def __str__(self):
        return "$EXTERN " + self.name


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


class DefinitionType(Function):

    def __init__(self, name, pattern, result, pos):
        super(DefinitionType, self).__init__(name, pos)
        self.pattern = pattern
        self.result = result

    def __eq__(self, other):
        return isinstance(other, DefinitionType) and self.name == other.name

    def __str__(self):
        return self.name + " " + str(self.pattern) + " = " + str(self.result)


class Sentence(object):

    def __init__(self, pattern, conditions, result, block):
        self.pattern = pattern
        self.conditions = conditions
        self.result = result
        self.block = block

    def __str__(self):
        result_str = str(self.pattern)
        if self.conditions:
            result_str += (", " + ",\n".join(list(map(str, self.conditions))))
        if self.conditions or self.block:
            result_str += (", " + str(self.result))
        if self.block:
            result_str += (": {" + ";\n".join(list(map(str, self.block))) + "}")
        if self.result is not None and not self.conditions and not self.block:
            result_str += (" = " + str(self.result))
        return result_str


class Condition(object):

    def __init__(self, result, pattern):
        self.result = result
        self.pattern = pattern

    def __str__(self):
        return str(self.result) + " : " + str(self.pattern)


class Expression(object):

    def __init__(self, terms):
        self.terms = terms

    def __eq__(self, other):
        return isinstance(other, Expression) and self.terms == other.terms

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return " ".join(list(map(str, self.terms)))


class Term(ABC):

    def __init__(self, value):
        self.value = value

    @abstractmethod
    def __str__(self):
        return str(self.value)


class Char(Term):

    def __init__(self, value):
        super(Char, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, Char) and self.value == other.value

    def __str__(self):
        return super(Char, self).__str__()


class Macrodigit(Term):

    def __init__(self, value):
        super(Macrodigit, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, Macrodigit) and self.value == other.value

    def __str__(self):
        return super(Macrodigit, self).__str__()


class CompoundSymbol(Term):

    def __init__(self, value):
        super(CompoundSymbol, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, CompoundSymbol) and self.value == other.value

    def __str__(self):
        return super(CompoundSymbol, self).__str__()


class StructuralBrackets(Term):

    def __init__(self, value):
        super(StructuralBrackets, self).__init__(value)

    def __eq__(self, other):
        return isinstance(other, StructuralBrackets) and self.value == other.value

    def __str__(self):
        return "(" + " ".join(list(map(str, self.value))) + ")"


class CallBrackets(Term):

    def __init__(self, func_name, pos, content):
        super(CallBrackets, self).__init__(func_name)
        self.pos = pos
        self.content = content

    def __str__(self):
        return "<" + self.value + " " + " ".join(list(map(str, self.content))) + ">"


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
        # return self.value
        if self.type_variable == Type.s:
            return "s." + str(self.index)
        elif self.type_variable == Type.t:
            return "t." + str(self.index)
        elif self.type_variable == Type.e:
            return "e." + str(self.index)
