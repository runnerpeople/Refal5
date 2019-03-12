#! python -v
# -*- coding: utf-8 -*-

from src.ast import *

from copy import deepcopy

import math
import sys

DEBUG_MODE = False


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
        return True
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
        return isinstance(other, SpecialVariable) and self.value == other.value and self.type_variable == other.type_variable

    def __str__(self):
        if self.type_variable == SpecialType.in_function:
            return "in(" + str(self.value) + ")"
        elif self.type_variable == SpecialType.out_function:
            return "out(" + str(self.value) + ")"
        else:
            return super(SpecialVariable, self).__str__()


class EqType(Enum):
    Term = 1
    Expr = 2


class Equation(object):

    def __init__(self, left_part, right_part, type_equation):
        self.left_part = left_part
        self.right_part = right_part
        self.type_equation = type_equation

    def __eq__(self, other):
        return isinstance(other, Equation) and self.left_part == other.left_part and self.right_part == other.right_part and \
               self.type_equation == other.type_equation

    def __str__(self):
        return str(self.left_part) + " : " + str(self.right_part)


class Substitution(object):

    def __init__(self, left_part, right_part):
        self.left_part = left_part
        self.right_part = right_part

    def __eq__(self, other):
        return isinstance(other, Substitution) and self.left_part == other.left_part and self.right_part == other.right_part

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

        self.default_format_function = []

        self.prepare_default_format_function()

        self.format_function = []
        self.substitution = []

        self.system = self.create_equation()
        # for eq in self.system:
        #     print(eq)
        #
        # sys.exit(1)

        if len(self.system) == 0:
            while True:
                format_substitution_function = []
                for function in ast.functions:
                    if isinstance(function, Definition):
                        for sentence in function.sentences:

                            format_substitution_function.append(Substitution(
                                Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                sentence.pattern))

                            format_substitution_function.append(Substitution(
                                Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                sentence.result))
                group_generalization = dict()
                for subst in [*format_substitution_function, *self.default_format_function]:
                    if subst.left_part not in group_generalization:
                        group_generalization[subst.left_part] = [deepcopy(subst.right_part)]
                    else:
                        group_generalization[subst.left_part].append(deepcopy(subst.right_part))

                format_functions = []
                for key_group in group_generalization.keys():
                    format_function = self.generalization(group_generalization[key_group])
                    format_functions.append(Substitution(key_group, format_function))

                format_functions_result = [format_function for format_function in format_functions
                                           if isinstance(format_function.left_part.terms[0], SpecialVariable)]

                substitution_result = []
                for format_function in format_functions:
                    if not isinstance(format_function.left_part.terms[0], SpecialVariable) \
                            and not format_function.right_part.terms == [SpecialVariable("@", SpecialType.none)]:
                        substitution_result.append(format_function)

                # self.substitution = [format_function for format_function in format_functions
                #                      if not isinstance(format_function.left_part.terms[0], SpecialVariable)
                #                      and not format_function.right_part.terms == [SpecialVariable("@", SpecialType.none)]
                #                      ]

                if self.is_fixed_point(self.format_function, format_functions_result):
                    break
                else:
                    self.format_function = format_functions_result
                    self.substitution = substitution_result
                    break
        else:
            while len(self.system) > 0:
                for k in range(len(self.system)):
                    eq = deepcopy(self.system[k])
                    # eq = self.system[k]
                    substitution = deepcopy(self.substitution)

                    eq.left_part = self.apply_substitution(eq.left_part, [*substitution, *self.format_function, *self.default_format_function])
                    eq.right_part = self.apply_substitution(eq.right_part, [*substitution, *self.format_function, *self.default_format_function])

                    if not (len(eq.right_part.terms) >= 1 and isinstance(eq.right_part.terms[0], SpecialVariable) and
                            eq.right_part.terms[0].type_variable == SpecialType.none) and \
                            len(eq.right_part.terms) >= 0:
                        status, substitution, self.system, eq = self.calculate_equation(eq, substitution, self.system)

                        if status == "Failure":
                            sys.stderr.write("There isn't solution for equation - %s" % self.system[k])
                            sys.exit(1)
                    else:
                        substitution = [Substitution(eq.left_part, eq.right_part)]

                    substitution = [subst for subst in substitution if not eq.left_part == eq.right_part]

                    ast = deepcopy(self.ast)

                    for function in ast.functions:
                        if isinstance(function, Definition):
                            for sentence in function.sentences:
                                sentence.pattern = self.apply_substitution(sentence.pattern,
                                                                           [*substitution, *self.format_function])
                                sentence.result = self.apply_substitution(sentence.result,
                                                                          [*substitution, *self.format_function])
                    format_substitution_function = []
                    for function in ast.functions:
                        if isinstance(function, Definition):
                            for sentence in function.sentences:

                                format_substitution_function.append(Substitution(
                                    Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                    sentence.pattern))

                                if all(self.contains_call(term) == False for term in sentence.result.terms):
                                    format_substitution_function.append(Substitution(
                                        Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                        sentence.result))
                    group_generalization = dict()
                    for subst in [*substitution, *format_substitution_function, *self.default_format_function]:
                        if subst.left_part not in group_generalization:
                            group_generalization[subst.left_part] = [deepcopy(subst.right_part)]
                        else:
                            group_generalization[subst.left_part].append(deepcopy(subst.right_part))

                    format_functions = []
                    for key_group in group_generalization.keys():
                        format_function = self.generalization(group_generalization[key_group])
                        format_functions.append(Substitution(key_group, format_function))

                    format_functions_result = [format_function for format_function in format_functions
                                               if isinstance(format_function.left_part.terms[0], SpecialVariable)]

                    substitution_result = []
                    for format_function in format_functions:
                        if not isinstance(format_function.left_part.terms[0], SpecialVariable) \
                                and not format_function.right_part.terms == [SpecialVariable("@", SpecialType.none)]:
                            substitution_result.append(format_function)

                    # self.substitution = [format_function for format_function in format_functions
                    #                      if not isinstance(format_function.left_part.terms[0], SpecialVariable)
                    #                      and not format_function.right_part.terms == [SpecialVariable("@", SpecialType.none)]
                    #                      ]

                    if self.is_fixed_point(self.format_function, format_functions_result):
                        self.system.remove(self.system[k])
                        # self.substitution = substitution_result
                        break
                    else:
                        self.format_function = format_functions_result
                        self.substitution = substitution_result
                        break

        self.print_format_function()

        if DEBUG_MODE:
            for substitution in self.substitution:
                print(substitution)

    def prepare_default_format_function(self):

        call_functions = []

        for function in self.ast.functions:
            if isinstance(function, Definition):
                for sentence in function.sentences:
                    for term_result in sentence.result.terms:
                        call_functions.extend(self.get_call(term_result))

        call_functions = list(set(call_functions))

        for definition_type_function in self.ast_type.functions:
            if isinstance(definition_type_function, DefinitionType):
                for call_function in call_functions:
                    if definition_type_function.name == call_function:
                        in_format = Expression([SpecialVariable(definition_type_function.name, SpecialType.in_function)])
                        out_format = Expression([SpecialVariable(definition_type_function.name, SpecialType.out_function)])
                        self.default_format_function.append(Substitution(in_format, definition_type_function.pattern))
                        self.default_format_function.append(Substitution(out_format, definition_type_function.result))


    def print_format_function(self):
        for function in self.ast.functions:
            if isinstance(function, Definition):
                in_format = Expression([SpecialVariable(function.name, SpecialType.in_function)])
                out_format = Expression([SpecialVariable(function.name, SpecialType.out_function)])
                print(function.name, end=' ')
                for format_function in self.format_function:
                    if format_function.left_part == in_format:
                        pattern = self.apply_substitution(format_function.right_part, [*self.substitution])
                        print(' '.join(list(map(self.print_term, pattern.terms))), end=' ')
                    if format_function.left_part == out_format:
                        print("=", end=' ')
                        result = self.apply_substitution(format_function.right_part, [*self.substitution])
                        print(' '.join(list(map(self.print_term, result.terms))), end='')
                print()

    def print_term(self, term):
        if isinstance(term, StructuralBrackets):
            output = '('
            output += ' '.join(list(map(self.print_term, term.value)))
            output += ')'
            return output
        if isinstance(term, Variable):
            return term.type_variable.name
        else:
            return term.__str__()

    def is_fixed_point(self, before_format, after_format):
        common_format = dict()
        for format_function in before_format:
            if format_function.left_part not in common_format:
                common_format[format_function.left_part] = [format_function.right_part]
            else:
                common_format[format_function.left_part].append(format_function.right_part)

        for format_function in after_format:
            if format_function.left_part not in common_format:
                common_format[format_function.left_part] = [format_function.right_part]
            else:
                common_format[format_function.left_part].append(format_function.right_part)

        for key_group in common_format.keys():
            if len(common_format[key_group]) == 1 or len(common_format[key_group][0].terms) != len(
                    common_format[key_group][1].terms):
                return False
            else:
                for i in range(len(common_format[key_group][0].terms)):

                    if isinstance(common_format[key_group][0].terms[i], StructuralBrackets) and \
                            isinstance(common_format[key_group][1].terms[i], StructuralBrackets):

                        before_common_format_brackets = [
                            Substitution(key_group, Expression(common_format[key_group][0].terms[i].value))]
                        after_common_format_brackets = [
                            Substitution(key_group, Expression(common_format[key_group][0].terms[i].value))]

                        if not self.is_fixed_point(before_common_format_brackets, after_common_format_brackets):
                            return False

                    elif not (isinstance(common_format[key_group][0].terms[i], Variable) and
                              isinstance(common_format[key_group][1].terms[i], Variable) and
                              common_format[key_group][0].terms[i].type_variable == common_format[key_group][1].terms[
                                  i].type_variable) and \
                            not common_format[key_group][0].terms[i] == common_format[key_group][1].terms[i]:

                        # print(isinstance(common_format[key_group][0].terms[i], Variable))
                        # print(isinstance(common_format[key_group][0].terms[i], Variable))
                        # if (isinstance(common_format[key_group][0].terms[i], Variable) and isinstance(
                        #         common_format[key_group][0].terms[i], Variable)):
                        #     print(
                        #         common_format[key_group][0].terms[i].type_variable == common_format[key_group][1].terms[
                        #             i].type_variable)
                        # print(common_format[key_group][0].terms[i] == common_format[key_group][1].terms[i])
                        # print(common_format[key_group][0].terms[i])
                        # print(common_format[key_group][1].terms[i])
                        return False

        return True

    def get_call(self, term):
        if isinstance(term, StructuralBrackets):
            term_call = []
            for terms in term.value:
                term_call.extend(self.get_call(terms))
            return term_call
        elif isinstance(term, CallBrackets):
            term_call = [term.value]
            for terms in term.content:
                term_call.extend(self.get_call(terms))
            return term_call
        elif isinstance(term, Variable):
            return []
        else:
            return []

    def contains_call(self, term):
        if isinstance(term, StructuralBrackets):
            return any(self.contains_call(term) for term in term.value)
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
        i = 0
        exprs = deepcopy(expr)
        while i < len(exprs.terms):
            j = i + 1
            exists_substitution = False
            while j <= len(exprs.terms):
                sub_expr = Expression(exprs.terms[i:j])
                for substitution in subst:
                    if substitution.left_part == sub_expr:
                        exists_substitution = True
                        res.extend(self.apply_substitution(substitution.right_part, subst).terms)
                        del exprs.terms[i:j]
                        break
                if exists_substitution:
                    break
                j += 1
            if exists_substitution:
                continue
            if isinstance(exprs.terms[i], (Variable, SpecialVariable)):
                exists_substitution = False
                for substitution in subst:
                    if type(substitution.left_part.terms[0]) == type(exprs.terms[i]) and substitution.left_part.terms[0] == exprs.terms[i]:
                        exists_substitution = True
                        res.extend(self.apply_substitution(substitution.right_part, subst).terms)
                if not exists_substitution:
                    res.append(exprs.terms[i])
            elif isinstance(exprs.terms[i], StructuralBrackets):
                res.extend([StructuralBrackets(self.apply_substitution(Expression(exprs.terms[i].value), subst).terms)])
            else:
                res.append(exprs.terms[i])
            i += 1
        return Expression(res)

    def create_equation(self):
        all_equations = []
        for function in self.ast.functions:
            if isinstance(function, Definition):
                equations = []
                for sentence in function.sentences:
                    for i in range(len(sentence.result.terms)):
                        if isinstance(sentence.result.terms[i], CallBrackets):
                            equations_new, _1, _2 = self.refactor(sentence.result.terms[i].content, sentence.result.terms[i].value)
                            equations.extend(equations_new)
                            sentence.result.terms[i] = SpecialVariable(sentence.result.terms[i].value,
                                                                       SpecialType.out_function)
                        elif isinstance(sentence.result.terms[i], StructuralBrackets):
                            equations_new, _1, _2 = self.refactor(sentence.result.terms[i].value, None)
                            equations.extend(equations_new)
                in_format = Expression([SpecialVariable(function.name, SpecialType.in_function)])
                out_format = Expression([SpecialVariable(function.name, SpecialType.out_function)])

                found_default_in_format = False
                found_default_out_format = False
                for definition_type_function in self.default_format_function:
                    if definition_type_function.left_part == in_format:
                        found_default_in_format = True
                    if definition_type_function.right_part == out_format:
                        found_default_out_format = True
                if not found_default_in_format:
                    self.format_function.append(
                        Substitution(Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                                     Expression([SpecialVariable("@", SpecialType.none)])))
                if not found_default_out_format:
                    self.format_function.append(
                        Substitution(Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                                     Expression([SpecialVariable("@", SpecialType.none)])))
                all_equations.extend(equations)
        return all_equations

    # match equation E : He
    def calculate_equation(self, equation, substitution, system):
        eq = deepcopy(equation)
        if eq.left_part.terms == [] and eq.right_part.terms == []:
            return "Success", substitution, system, eq
        else:
            if eq.type_equation == EqType.Term:

                term_left = eq.left_part.terms[0]
                term_right = eq.right_part.terms[0]

                if isinstance(term_right, Variable) and isinstance(term_left, Variable) and term_left == term_right:
                    return "Success", substitution, system, eq
                if is_symbol(term_left) and is_symbol(term_right) and term_left == term_right:
                    return "Success", substitution, system, eq
                elif isinstance(term_right, Variable) and term_right.type_variable == Type.t:
                    substitution.append(Substitution(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, system, eq
                elif (isinstance(term_right, Variable) and term_right.type_variable == Type.s) or is_symbol(term_right):
                    substitution.append(Substitution(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, system, eq
                elif isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
                    eq.type_equation = EqType.Expr
                    eq.left_part.terms = Expression(term_left.value).terms
                    eq.right_part.terms = Expression(term_right.value).terms
                    return self.calculate_equation(eq, substitution, system)
                elif isinstance(term_right, StructuralBrackets) and isinstance(term_left,
                                                                               Variable) and term_left.type_variable == Type.t:
                    substitution.append(Substitution(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, system, eq
                else:
                    return "Failure", [], system, eq

            else:
                if len(eq.left_part.terms) > 0 and is_hard_term(eq.left_part.terms[0]) \
                        and len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[0]):

                    subst = deepcopy(substitution)
                    syst = deepcopy(system)

                    status, subst, syst, e = self.calculate_equation(Equation(Expression([eq.left_part.terms[0]]),
                                                                              Expression([eq.right_part.terms[0]]),
                                                                              EqType.Term), subst, syst)

                    eq.left_part.terms = eq.left_part.terms[1:]
                    eq.right_part.terms = eq.right_part.terms[1:]

                    if status == "Success":
                        substitution = subst
                        system = syst
                        return self.calculate_equation(eq,substitution,system)
                    else:
                        return "Failure", substitution, system, eq

                elif len(eq.left_part.terms) > 0 and is_hard_term(eq.left_part.terms[-1]) \
                        and len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[-1]):

                    subst = deepcopy(substitution)
                    syst = deepcopy(system)

                    status, subst, syst, e = self.calculate_equation(Equation(Expression([eq.left_part.terms[-1]]),
                                                                              Expression([eq.right_part.terms[-1]]),
                                                                              EqType.Term), subst, syst)

                    eq.left_part.terms = eq.left_part.terms[:-1]
                    eq.right_part.terms = eq.right_part.terms[:-1]

                    if status == "Success":
                        substitution = subst
                        system = syst
                        return self.calculate_equation(eq, substitution, system)
                    else:
                        return "Failure", substitution, system, eq

                if len(eq.left_part.terms) == 0:

                    if len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[0]):
                        # self.isError = True
                        return "Failure", [], system, eq

                    if len(eq.right_part.terms) == 0:
                        return "Success", substitution, system, eq

                    if any(isinstance(term, Variable) and term.type_variable == Type.e for term in
                           eq.right_part.terms):
                        return "Success", substitution, system, eq

                    return "Undefined", [], system

                if len(eq.left_part.terms) > 0 and isinstance(eq.left_part.terms[0], Variable) and \
                        eq.left_part.terms[0].type_variable == Type.e and len(
                    eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[0]):
                    left_part = eq.left_part.terms.pop(0)
                    first_substitution = [*substitution, Substitution(Expression([left_part]), Expression([]))]

                    syst = deepcopy(system)

                    status, subst, syst, equation_new = self.calculate_equation(eq, first_substitution, syst)
                    if status == "Failure":
                        index = generate_index()
                        t_variable = Variable("generated%d".format(index), Type.t, None, index)
                        index = generate_index()
                        e_variable = Variable("generated%d".format(index), Type.e, None, index)
                        second_substitution = [*substitution,
                                               Substitution(Expression([left_part]),
                                                            Expression([t_variable, e_variable]))]
                        eq.left_part.terms.insert(0, t_variable)
                        eq.left_part.terms.insert(1, e_variable)
                        return self.calculate_equation(eq, second_substitution, syst)
                    else:
                        return status, subst, syst, equation_new
                if len(eq.left_part.terms) > 0 and isinstance(eq.left_part.terms[-1], Variable) and \
                        eq.left_part.terms[-1].type_variable == Type.e and len(
                    eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[-1]):
                    left_part = eq.left_part.terms.pop()
                    first_substitution = [*substitution, Substitution(Expression([left_part]), Expression([]))]

                    syst = deepcopy(system)

                    status, subst, syst, equation_new = self.calculate_equation(eq, first_substitution, syst)
                    if status == "Failure":
                        index = generate_index()
                        t_variable = Variable("generated%d".format(index), Type.t, None, index)
                        index = generate_index()
                        e_variable = Variable("generated%d".format(index), Type.e, None, index)
                        second_substitution = [*substitution,
                                               Substitution(Expression([left_part]),
                                                            Expression([e_variable, t_variable]))]
                        eq.left_part.terms.insert(len(eq.left_part.terms), e_variable)
                        eq.left_part.terms.insert(len(eq.left_part.terms), t_variable)
                        return self.calculate_equation(eq, second_substitution, system)
                    else:
                        return status, subst, syst, equation_new

                if len(eq.right_part.terms) == 0:
                    if all(isinstance(term, Variable) and term.type_variable == Type.e for term in
                           eq.left_part.terms):
                        for term in eq.left_part.terms:
                            substitution.append(Substitution(eq.left_part, Expression([])))
                        return "Success", substitution, system, eq
                    else:
                        return "Failure", [], system, eq

                # exists_e_variable_out = False
                # for term in equation.right_part.terms:
                #     if isinstance(term, Variable) and term.type_variable == Type.e:
                #         exists_e_variable_out = True
                #         substitution.append(Substitution(equation.left_part, Expression(term)))
                #         break
                # if exists_e_variable_out:
                if len(eq.right_part.terms) > 0:
                    if all(isinstance(term, Variable) and term.type_variable == Type.e for term in
                           eq.right_part.terms):
                        # substitution.append()
                        return "Success", substitution, system, eq
                    else:
                        return "Failure", [], system, eq

                else:
                    return "Undefined", [], system, eq

    def refactor(self, terms, func_name):
        equations = []
        i = 0
        while i < len(terms):
            if isinstance(terms[i], CallBrackets):
                equations_new, _, flag = self.refactor(terms[i].content, terms[i].value)
                terms[i] = SpecialVariable(terms[i].value, SpecialType.out_function)
                equations.extend(equations_new)
            elif isinstance(terms[i], StructuralBrackets):
                equations_new, terms_new, flag = self.refactor(terms[i].value, None)
                terms[i] = StructuralBrackets(terms_new)
                if flag:
                    equations.extend(equations_new)
            i += 1
        if func_name is not None:
            in_variable = Expression([SpecialVariable(func_name, SpecialType.in_function)])
            return [Equation(Expression(terms), in_variable, EqType.Expr), *equations], terms, True
        else:
            return [], terms, False


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
            return StructuralBrackets(self.generalization([Expression(term_left.value), Expression(term_right.value)]).terms)
        if isinstance(term_left, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.t, None, index)
        if isinstance(term_right, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.s, None, index)

    def generalization_term(self, terms):
        while len(terms) > 1:
            term = self.generalization_term_rec(terms.pop(), terms.pop())
            if isinstance(term, Expression):
                terms.extend(term.terms)
            else:
                terms.append(term)
        return terms[0]

    def generalization(self, patterns):
        if len(patterns) > 1:
            for pattern in patterns:
                special_value = any(
                    isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none for term in
                    pattern.terms)
                if special_value:
                    patterns.remove(pattern)
                    return self.generalization(patterns)
        elif len(patterns) == 1:
            for term in patterns[0].terms:
                if isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none:
                    return Expression([term])

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
                        pattern.terms.pop()
                    return Expression([*self.generalization(patterns).terms, *right_t])
