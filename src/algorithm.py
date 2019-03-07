#! python -v
# -*- coding: utf-8 -*-

from src.ast import *

from copy import deepcopy

import math

DEBUG_MODE = True


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
        return self.value == other.value and self.type_variable == other.type_variable

    def __str__(self):
        if self.type_variable == SpecialType.in_function:
            return "in(" + str(self.value) + ")"
        elif self.type_variable == SpecialType.out_function:
            return "out(" + str(self.value) + ")"
        else:
            return super(SpecialVariable, self).__str__()


class Equation(object):

    def __init__(self, left_part, right_part):
        self.left_part = left_part
        self.right_part = right_part

    def __eq__(self, other):
        return self.left_part == other.left_part and self.right_part == other.right_part

    def __str__(self):
        return str(self.left_part) + " : " + str(self.right_part)


class Substitution(object):

    def __init__(self, left_part, right_part):
        self.left_part = left_part
        self.right_part = right_part

    def __eq__(self, other):
        return self.left_part == other.left_part and self.right_part == other.right_part

    def __str__(self):
        return str(self.left_part) + " -> " + str(self.right_part)


class Calculation(object):

    def __init__(self, ast, ast_type):
        self.ast = deepcopy(ast)
        self.ast_type = deepcopy(ast_type)

        self.isError = False

        self.prepare_func()

        if DEBUG_MODE:
            print(self.ast)

        self.format_function = []
        self.substitution = []

        self.equation = self.create_equation()

        while len(self.equation) > 0:
            for equation in self.equation:
                eq = deepcopy(equation)
                substitution = []
                eq.left_part = self.apply_substitution(eq.left_part, [*substitution, *self.format_function])
                eq.right_part = self.apply_substitution(eq.right_part, [*substitution, *self.format_function])

                if not (len(eq.right_part.terms) >= 1 and isinstance(eq.right_part.terms[0], SpecialVariable) and
                                                       eq.right_part.terms[0].type_variable == SpecialType.none) and \
                        len(eq.right_part.terms) >= 0:
                    self.calculate_equation(eq, substitution)
                else:
                    substitution = [Substitution(eq.left_part, eq.right_part)]


                ast = deepcopy(self.ast)

                for function in ast.functions:
                    if isinstance(function, Definition):
                        for sentence in function.sentences:
                            sentence.pattern = self.apply_substitution(sentence.pattern, [*substitution, *self.format_function])
                            sentence.result = self.apply_substitution(sentence.result, [*substitution, *self.format_function])


                for function in ast.functions:
                    if isinstance(function, Definition):
                        for sentence in function.sentences:

                            self.format_function.append(Substitution(
                                Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                sentence.pattern))

                            if all(self.contains_call(term) == False for term in sentence.result.terms):
                                self.format_function.append(Substitution(
                                    Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                    sentence.result))
                group_generalization = dict()
                for subst in [*substitution, *self.format_function]:
                    if subst.left_part not in group_generalization:
                        group_generalization[subst.left_part] = [subst.right_part]
                    else:
                        group_generalization[subst.left_part].append(subst.right_part)

                format_functions = []
                for key_group in group_generalization.keys():
                    format_function = self.generalization(group_generalization[key_group])
                    format_functions.append(Substitution(key_group, format_function))

                format_functions = [format_function for format_function in format_functions
                                    if isinstance(format_function.left_part.terms[0],SpecialVariable)]

                if format_functions == self.format_function:
                    self.equation.remove(equation)
                else:
                    self.format_function = format_functions
                    break


    def contains_call(self, term):
        if isinstance(term, StructuralBrackets):
            return any(isinstance(term, CallBrackets) for term in term.value)
        elif isinstance(term, CallBrackets):
            return True
        elif isinstance(term, Variable):
            return False
        else:
            return False

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

    def apply_substitution(self, expr, subst):
        res = []
        for term in expr.terms:
            if isinstance(term, (Variable, SpecialVariable)):
                exists_substitution = False
                for substitution in subst:
                    if substitution.left_part.terms[0] == term:
                        exists_substitution = True
                        res += substitution.right_part.terms
                if not exists_substitution:
                    res += [term]
            elif isinstance(term, StructuralBrackets):
                res += [StructuralBrackets(self.apply_substitution(Expression(term.value), subst).terms)]
            else:
                res += [term]
        return Expression(res)

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
                                equations.extend(self.refactor(term[j].content, term[j].value))
                                # term[j] = SpecialVariable(term[j].value, SpecialType.out_function)
                            elif isinstance(term[j], StructuralBrackets):
                                equations.extend(self.refactor(term[j].value, None))
                self.format_function.append(
                    Substitution(Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                 Expression([SpecialVariable("@", SpecialType.none)])))
                self.format_function.append(
                    Substitution(Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                 Expression([SpecialVariable("@", SpecialType.none)])))
                all_equations.extend(equations)
        return all_equations

    def term_match(self, term_left, term_right, substitution):
        if is_symbol(term_left) and is_symbol(term_right) and term_left == term_right:
            return "Success"
        elif isinstance(term_right, Variable) and term_right.type_variable == Type.t:
            self.substitution.append(Substitution(term_left, term_right))
            return "Success"
        elif (isinstance(term_right, Variable) and term_right.type_variable == Type.s) or is_symbol(term_right):
            self.substitution.append(Substitution(term_left, term_right))
            return "Success"
        elif isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
            self.calculate_equation(Equation(term_left.value, term_right.value), substitution)
            return "Success"
        else:
            return "Failure"

    # match equation E : He
    def calculate_equation(self, equation, substitution):
        if equation.left_part.terms == [] and equation.right_part.terms == []:
            return "Success"
        else:

            if len(equation.left_part.terms) > 0 and is_hard_term(equation.left_part.terms[0]) \
                    and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[0]):
                status = self.term_match(equation.left_part.terms.pop(0), equation.right_part.terms.pop(0),
                                         substitution)
                return self.calculate_equation(equation, substitution)

            if len(equation.left_part.terms) > 0 and is_hard_term(equation.left_part.terms[-1]) \
                    and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[-1]):
                status = self.term_match(equation.left_part.terms.pop(), equation.right_part.terms.pop(),
                                         substitution)
                return self.calculate_equation(equation, substitution)

            if len(equation.left_part.terms) == 0:

                if len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[0]):
                    # self.isError = True
                    return "Failure"

                if len(equation.right_part.terms) == 0:
                    return "Success"

                if any(isinstance(term, Variable) and term.type_variable == Type.e for term in equation.right_part.terms):
                    return "Success"

                return "Undefined"

            if len(equation.left_part.terms) > 0 and isinstance(equation.left_part.terms[0], Variable) and \
                    equation.left_part.terms[0].type_variable == Type.e and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[0]):
                left_part = equation.left_part.terms.pop(0)
                first_substitution = [*substitution, Substitution(left_part, Expression([]))]
                status = self.calculate_equation(equation, first_substitution)
                if status == "Failure":
                    index = generate_index()
                    t_variable = Variable("generated%d".format(index), Type.t, None, index)
                    index = generate_index()
                    e_variable = Variable("generated%d".format(index), Type.e, None, index)
                    second_substitution = [*substitution,
                                           Substitution(left_part, Expression([t_variable, e_variable]))]
                    equation.left_part.terms.insert(0, t_variable)
                    equation.left_part.terms.insert(1, e_variable)
                    return self.calculate_equation(equation, second_substitution)
            if len(equation.left_part.terms) > 0 and isinstance(equation.left_part.terms[-1], Variable) and \
                    equation.left_part.terms[-1].type_variable == Type.e and len(equation.right_part.terms) > 0 and is_hard_term(equation.right_part.terms[-1]):
                left_part = equation.left_part.terms.pop()
                first_substitution = [*substitution, Substitution(left_part, Expression([]))]
                status = self.calculate_equation(equation, first_substitution)
                if status == "Failure":
                    index = generate_index()
                    t_variable = Variable("generated%d".format(index), Type.t, None, index)
                    index = generate_index()
                    e_variable = Variable("generated%d".format(index), Type.e, None, index)
                    second_substitution = [*substitution,
                                           Substitution(left_part, Expression([t_variable, e_variable]))]
                    equation.left_part.terms.insert(len(equation.left_part.terms) - 2, t_variable)
                    equation.left_part.terms.insert(len(equation.left_part.terms) - 2, e_variable)
                    return self.calculate_equation(equation, second_substitution)

            if len(equation.right_part.terms) == 0:
                if all(isinstance(term, Variable) and term.type_variable == Type.e for term in equation.left_part.terms):
                    for term in equation.left_part.terms:
                        substitution.append(Substitution(equation.left_part, Expression([])))
                    return "Success"
                else:
                    return "Failure"

            # exists_e_variable_out = False
            # for term in equation.right_part.terms:
            #     if isinstance(term, Variable) and term.type_variable == Type.e:
            #         exists_e_variable_out = True
            #         substitution.append(Substitution(equation.left_part, Expression(term)))
            #         break
            # if exists_e_variable_out:
            if len(equation.right_part.terms) > 0:
                if all(isinstance(term, Variable) and term.type_variable == Type.e for term in equation.right_part.terms):
                    return "Success"
                else:
                    return "Failure"

            else:
                return "Undefined"

    def refactor(self, terms, func_name):
        equations = []
        left_part = []
        for i in range(len(terms)):
            term = [terms[i]]
            for j in range(len(term)):
                if isinstance(term[j], CallBrackets):
                    equations.extend(self.refactor(term[j].content, term[j].value))
                    term[j] = SpecialVariable(term[j].value, SpecialType.out_function)
                elif isinstance(terms[j], StructuralBrackets):
                    terms[j] = self.refactor(terms[j].value, func_name)
                left_part.append(term[j])
        if func_name is not None:
            in_variable = Expression([SpecialVariable(func_name, SpecialType.in_function)])
            return [Equation(Expression(left_part), in_variable), *equations]
        else:
            return equations

    def generalization_term_rec(self, term_left, term_right):
        # if isinstance(term_left, SpecialVariable) and term_left.type_variable == SpecialType.none:
        #     return term_left
        # if isinstance(term_right, SpecialVariable) and term_right.type_variable == SpecialType.none:
        #     return term_right
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
            return self.generalization([term_left.value, term_right.value])
        if isinstance(term_left, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.t, None, index)
        if isinstance(term_right, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.s, None, index)

    def generalization_term(self, terms):
        while len(terms) > 1:
            term = self.generalization_term_rec(terms.pop(), terms.pop())
            terms.append(term)
        return terms[0]

    def generalization(self, patterns):
        if len(patterns) > 1:
            for pattern in patterns:
                special_value = any(isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none for term in pattern.terms)
                if special_value:
                    patterns.remove(pattern)
                    return self.generalization(patterns)

        all_empty = all(len(pattern.terms) == 0 for pattern in patterns)
        any_empty = any(len(pattern.terms) == 0 for pattern in patterns)

        if all_empty:
            return Expression([])
        elif any_empty:
            index = generate_index()
            return Expression([Variable("generated%d".format(index), Type.e, None, index)])
        else:
            left = [pattern.terms[0] for pattern in patterns]
            right = [pattern.terms[-1] for pattern in patterns]

            left_e = any(isinstance(term, Variable) and term.type_variable == Type.e for term in left)
            right_e = any(isinstance(term, Variable) and term.type_variable == Type.e for term in right)

            if left_e:
                if right_e:
                    index = generate_index()
                    return Expression([Variable("generated%d".format(index), Type.e, None, index)])
                else:
                    for pattern in patterns:
                        pattern.terms.pop()
                    return Expression([*self.generalization(patterns).terms, self.generalization_term(right)])
            else:
                if right_e:
                    for pattern in patterns:
                        pattern.terms.pop(0)
                    return Expression([self.generalization_term(left), *self.generalization(patterns).terms])
                else:
                    left_t = [self.generalization_term(left)]
                right_t = [self.generalization_term(right)]
                if calc_complexity(left_t) >= calc_complexity(right_t):
                    for pattern in patterns:
                        pattern.terms.pop(0)
                    return Expression([*left_t, *self.generalization(patterns).terms])
                else:
                    for pattern in patterns:
                        pattern.terms.pop(0)
                    return Expression([*self.generalization(patterns), *right_t])
