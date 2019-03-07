#! python -v
# -*- coding: utf-8 -*-

from src.tokens import *
from src.ast import *

from copy import deepcopy

import math


def generate_index():
    generate_index.counter += 1
    return generate_index.counter


generate_index.counter = -1


def change_variable_index(variable, index, sentence_index):
    variable.index = index
    variable.sentence_index = sentence_index
    return variable


def is_hard_term(term):
    if isinstance(term, Variable):
        if term.type_variable == Type.e:
            return False
        else:
            return True
    elif isinstance(term, CallBrackets):
        return False
    else:
        return True


def is_symbol(term):
    if isinstance(term, (CompoundSymbol, Macrodigit, Char)):
        return True
    else:
        return False


def calc_complexity(terms):
    complexity = 0
    for term in terms:
        if isinstance(term, Variable) and term.type_variable == Type.s:
            complexity += 2
        elif isinstance(term, Variable) and term.type_variable == Type.t:
            complexity += 1
        elif isinstance(term, Variable) and term.type_variable == Type.e:
            complexity -= 1
        elif is_symbol(term):
            complexity += 3
        elif isinstance(term, StructuralBrackets):
            complexity += 2
        elif isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none:
            complexity += math.inf
    return complexity + 1


class SpecialType(Enum):
    in_function = 1
    out_function = 2
    none = 3


class SpecialVariable(Term):

    def __init__(self, value, type_variable, sentence_index=-1):
        super(SpecialVariable, self).__init__(value)
        self.type_variable = type_variable
        self.sentence_index = sentence_index

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        if self.type_variable == SpecialType.in_function:
            return "in(" + str(self.value) + ")"
        elif self.type_variable == SpecialType.out_function:
            return "out(" + str(self.value) + ")"
        else:
            return super(SpecialVariable, self).__str__()


class Equation(object):

    def __init__(self, left_part, right_part, function):
        self.left_part = left_part
        self.right_part = right_part

        self.function = deepcopy(function)

    def __str__(self):
        return str(self.left_part) + " : " + str(self.right_part)


class Substitution(object):

    def __init__(self, left_part, right_part):
        self.left_part = left_part
        self.right_part = right_part

    def __str__(self):
        return str(self.left_part) + " -> " + str(self.right_part)


class Calculation(object):

    def __init__(self, ast, ast_type):
        self.ast = deepcopy(ast)
        self.ast_type = deepcopy(ast_type)

        self.isError = False

        self.prepare_func()

        print(self.ast)

        self.substitution = []

        self.equation = self.create_equation()

        while len(self.equation) > 0:
            equation = self.equation.pop()
            self.substitute_function(equation)
            while True:
                status = self.calculate_equation(equation)
                self.substitute_function(equation)

                self.substitute_sentences(equation.function.sentences, [equation])

    def substitute_sentences(self, sentences, equation):
        for sentence in sentences:
            for i in range(len(sentence.pattern.terms)):
                substitution = self.substitute_term(sentence.pattern.terms[i], equation)
                if isinstance(substitution, Expression):
                    sentence.pattern.terms[i:i] = substitution.terms
                else:
                    sentence.pattern.terms[i] = [substitution]
            for condition in sentence.conditions:
                for i in range(len(condition.pattern.terms)):
                    substitution = self.substitute_term(condition.pattern.terms[i], equation)
                    if isinstance(substitution, Expression):
                        condition.pattern.terms[i:i] = substitution.terms
                    else:
                        condition.pattern.terms[i] = [substitution]
                for i in range(len(condition.result.terms)):
                    substitution = self.substitute_term(sentence.pattern.terms[i], equation)
                    if isinstance(substitution, Expression):
                        condition.result.terms[i:i] = substitution.terms
                    else:
                        condition.result.terms[i] = [substitution]
            if sentence.block:
                self.substitute_sentences(sentence.block, equation)
            for i in range(len(sentence.result.terms)):
                substitution = self.substitute_term(sentence.result.terms[i], equation)
                if isinstance(substitution, Expression):
                    sentence.result.terms[i:i] = substitution.terms
                else:
                    sentence.result.terms[i] = [substitution]

    def substitute_term(self, term, equation):
        if isinstance(term, StructuralBrackets):
            return StructuralBrackets(self.substitute_term(term.value[0], equation))
        else:
            for substitution in equation:
                if isinstance(term, Variable) and substitution.left_part.terms[0].type_variable == term.type_variable \
                        and substitution.left_part.terms[0].index == term.index:
                    return substitution.right_part
            return term

    def substitute_function(self, equation):

        for i in range(len(equation.right_part.terms)):
            for substitution in self.substitution:

                if substitution.left_part.terms[0] == equation.right_part.terms[i]:
                    equation.right_part = Expression([*equation.right_part.terms[:i],
                                                      *substitution.right_part.terms,
                                                      *equation.right_part.terms[i + 1:]])
                    continue
        for i in range(len(equation.left_part.terms)):
            for substitution in self.substitution:

                if substitution.left_part.terms[0] == equation.left_part.terms[i]:
                    equation.left_part = Expression([*equation.left_part.terms[:i],
                                                     *substitution.left_part.terms,
                                                     *equation.left_part.terms[i + 1:]])
                    continue

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
            return [term]
        else:
            return []

    def get_term(self, term):
        if isinstance(term, StructuralBrackets):
            terms = []
            for t in term.value:
                terms.extend(self.get_term(t))
            return terms
        else:
            return [term]

    def term_match(self, term_left, term_right):
        if is_symbol(term_left) and is_symbol(term_right) and term_left == term_right:
            return "Success"
        elif isinstance(term_right, Variable) and term_right.type_variable == Type.t:
            self.substitution.append(Substitution(term_left, term_right))
            return "Success"
        elif (isinstance(term_right, Variable) and term_right.type_variable == Type.s) or is_symbol(term_right):
            self.substitution.append(Substitution(term_left, term_right))
            return "Success"
        elif isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
            self.calculate_equation(Equation(term_left.value, term_right.value))
            return "Success"
        else:
            return "Failure"

    # match equation E : He
    def calculate_equation(self, equation):
        if equation.left_part.terms == [] and equation.right_part.terms == []:
            return "Success"
        else:
            exists_e_variable = False
            for term in equation.right_part.terms:
                if isinstance(term, Variable) and term.type_variable == Type.e:
                    exists_e_variable = True
                    self.substitution.append(Substitution(equation.left_part, term))
                    break
            if exists_e_variable:
                return "Success"

            elif len(equation.left_part.terms) > 0 and is_hard_term(equation.left_part.terms[0]) \
                    and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[0]):
                status = self.term_match(equation.left_part.pop(0), equation.right_part.pop(0))
                if status == "Failure":
                    self.isError = True
                self.calculate_equation(equation)

            elif len(equation.left_part.terms) > 0 and is_hard_term(equation.left_part.terms[-1]) \
                    and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[-1]):
                status = self.term_match(equation.left_part.pop(), equation.right_part.pop())
                if status == "Failure":
                    self.isError = True
                self.calculate_equation(equation)

            else:
                terms = [term for term in equation.right_part.terms if isinstance(term, SpecialVariable)
                         and term.type_variable == SpecialType.none]
                if terms:
                    return "Restart"
                else:
                    return "Undefined"

    def prepare_func(self):
        index = 0
        for function in self.ast.functions:
            if isinstance(function, Definition):
                self.prepare_func_rec(function.sentences, index)

    def prepare_func_rec(self, sentences, index):
        for sentence in sentences:
            index += 1
            variable_dict_index = dict()
            for term in sentence.pattern.terms:
                variables = self.get_variables(term)
                for i in range(len(variables)):
                    if variables[i].value not in variable_dict_index:
                        variable_dict_index[variables[i].value] = generate_index()
                    variables[i] = change_variable_index(variables[i], variable_dict_index[variables[i].value], index)
            for condition in sentence.conditions:
                for term_condition in condition.pattern.terms:
                    variables = self.get_variables(term_condition)
                    for i in range(len(variables)):
                        if variables[i].value not in variable_dict_index:
                            variable_dict_index[variables[i].value] = generate_index()
                        variables[i] = change_variable_index(variables[i], variable_dict_index[variables[i].value],
                                                             index)
                for term_result in condition.result.terms:
                    variables = self.get_variables(term_result)
                    for i in range(len(variables)):
                        if variables[i].value not in variable_dict_index:
                            variable_dict_index[variables[i].value] = generate_index()
                        variables[i] = change_variable_index(variables[i], variable_dict_index[variables[i].value],
                                                             index)
            if sentence.block:
                self.prepare_func_rec(sentence.block, 0)
            for term_result in sentence.result.terms:
                variables = self.get_variables(term_result)
                for i in range(len(variables)):
                    if variables[i].value not in variable_dict_index:
                        variable_dict_index[variables[i].value] = generate_index()
                    variables[i] = change_variable_index(variables[i], variable_dict_index[variables[i].value], index)

    def create_equation(self):
        all_equations = []
        for function in self.ast.functions:
            if isinstance(function, Definition):
                equations = []
                for sentence in function.sentences:
                    for i in range(len(sentence.result.terms)):
                        term = [sentence.result.terms[i]]
                        for j in range(len(term)):
                            if isinstance(term[j], CallBrackets):
                                equations.extend(self.refactor(term[j].content, term[j].value, function))
                                # term[j] = SpecialVariable(term[j].value, SpecialType.out_function)
                            elif isinstance(term[j], StructuralBrackets):
                                equations.extend(self.refactor(term[j].value, None, function))
                    if equations:
                        self.substitution.append(
                            Substitution(Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                         Expression([SpecialVariable("@", SpecialType.none)])))
                        self.substitution.append(
                            Substitution(Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                         Expression([SpecialVariable("@", SpecialType.none)])))
                    # else:
                    #     self.old_substitution.append(
                    #         Substitution(Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                    #                      sentence.pattern))
                    #     self.old_substitution.append(
                    #         Substitution(Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                    #                      sentence.result))
                all_equations.extend(equations)
        return all_equations

    def refactor(self, terms, func_name, function):
        equations = []
        left_part = []
        for i in range(len(terms)):
            term = [terms[i]]
            for j in range(len(term)):
                if isinstance(term[j], CallBrackets):
                    equations.extend(self.refactor(term[j].content, term[j].value, function))
                    term[j] = SpecialVariable(term[j].value, SpecialType.out_function)
                elif isinstance(terms[j], StructuralBrackets):
                    terms[j] = self.refactor(terms[j].value, func_name, function)
                left_part.append(term[j])
        if func_name is not None:
            in_variable = Expression([SpecialVariable(func_name, SpecialType.in_function)])
            return [Equation(Expression(left_part), in_variable, function), *equations]
        else:
            return equations

    def generalization_term(self, term_left, term_right):
        if isinstance(term_left, SpecialVariable) and term_left.type_variable == SpecialType.none:
            return term_left
        if isinstance(term_right, SpecialVariable) and term_right.type_variable == SpecialType.none:
            return term_right
        if is_symbol(term_left) and is_symbol(term_right):
            if term_left == term_right:
                return term_left
            else:
                index = generate_index()
                return Variable("generated%d".format(index), Type.s, None, index)
        if (isinstance(term_left, Variable) and term_left.type_variable == Type.s) and is_symbol(term_right):
            return term_left
        if (isinstance(term_right, Variable) and term_right.type_variable == Type.s) and is_symbol(term_left):
            return term_right
        if (isinstance(term_right, Variable) and term_right.type_variable == Type.s) and \
                (isinstance(term_left, Variable) and term_left.type_variable == Type.s):
            return term_left
        if isinstance(term_left, Variable) and term_left.type_variable == Type.t:
            return term_left
        if isinstance(term_right, Variable) and term_right.type_variable == Type.t:
            return term_right
        if isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
            return self.generalization(term_left.value, term_right.value)
        if isinstance(term_left, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.t, None, index)
        if isinstance(term_right, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.s, None, index)

    def generalization(self, pattern_first, pattern_last):
        result = []
        if len(pattern_first.terms) >= 1 and len(pattern_last.terms) >= 1:
            term_left_first = pattern_first.terms[0]
            term_left_last = pattern_last.terms[0]

            if len(pattern_first.terms) >= 1 and len(pattern_last.terms) >= 1:
                term_right_first = pattern_first.terms[-1]
                term_right_last = pattern_last.terms[-1]

                if (isinstance(term_left_first, Variable) and term_left_first.type_variable == Type.e) or \
                        (isinstance(term_left_last, Variable) and term_left_last.type_variable == Type.e):
                    if isinstance(term_right_first, StructuralBrackets) or isinstance(term_right_last,
                                                                                      StructuralBrackets):
                        index = generate_index()
                        variable = Variable("generated%d".format(index), Type.e, None, index)
                        result.append(StructuralBrackets([variable]))
                    else:
                        index = generate_index()
                        variable = Variable("generated%d".format(index), Type.e, None, index)
                        result.append(variable)

                elif (isinstance(term_right_first, Variable) and term_right_first.type_variable == Type.e) or \
                        (isinstance(term_right_last, Variable) and term_right_last.type_variable == Type.e):
                    if isinstance(term_left_first, StructuralBrackets) or isinstance(term_left_last,
                                                                                     StructuralBrackets):
                        index = generate_index()
                        variable = Variable("generated%d".format(index), Type.e, None, index)
                        result.append(StructuralBrackets([variable]))
                    else:
                        index = generate_index()
                        variable = Variable("generated%d".format(index), Type.e, None, index)
                        result.append(variable)

                else:

                    result_generalization_term_right = self.generalization_term(term_right_first, term_right_last)
                    result_generalization_term_left = self.generalization_term(term_left_first, term_left_last)

                    if calc_complexity(result_generalization_term_left) >= calc_complexity(
                            result_generalization_term_right):
                        result.append(result_generalization_term_left)
                        pattern_first.terms.pop(0)
                        pattern_last.terms.pop(0)
                        result.extend(self.generalization(pattern_first, pattern_last))
                    else:
                        result.append(result_generalization_term_right)
                        pattern_first.terms.pop()
                        pattern_last.terms.pop()
                        result.extend(self.generalization(pattern_first, pattern_last))
        if len(pattern_first.terms) >= 1 or len(pattern_last.terms) >= 1:
            index = generate_index()
            variable = Variable("generated%d".format(index), Type.e, None, index)
            result.append(variable)

        return result
