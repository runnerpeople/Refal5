#! python -v
# -*- coding: utf-8 -*-

from refal.ast import *
from refal.constants import *
from refal.utils import *

from copy import deepcopy

import math
import sys


def change_variable_index(variable, index):
    if isinstance(variable, Variable):
        variable.index = index
        return variable
    else:
        raise ValueError("variable must be instance of class Variable (s.Index, t.Index, e.Index)")


def change_variable_index_and_index_sentence(variable, index, sentence_index):
    if isinstance(variable, Variable):
        variable.index = index
        variable.sentence_index = sentence_index
        return variable
    else:
        raise ValueError("variable must be instance of class Variable (s.Index, t.Index, e.Index)")


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


def append_char_term(terms):
    i = 0
    append_terms = []
    while i < len(terms):
        if isinstance(terms[i], Char):
            j = i + 1
            value = terms[i].value
            while j < len(terms):
                if not isinstance(terms[j], Char):
                    append_terms.append(Char("'" + value.replace("'", "") + "'"))
                    value = ""
                    i = j - 1
                    break
                else:
                    value += terms[j].value
                    j += 1
            if value != "" and j == len(terms):
                append_terms.append(Char("'" + value.replace("'", "") + "'"))
                i = j
        elif isinstance(terms[i], CallBrackets):
            append_terms.append(CallBrackets(terms[i].value, terms[i].pos, append_char_term(terms[i].content)))
        elif isinstance(terms[i], StructuralBrackets):
            append_terms.append(StructuralBrackets(append_char_term(terms[i].value)))
        else:
            append_terms.append(terms[i])
        i += 1
    return append_terms


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
        return isinstance(other, SpecialVariable) \
               and self.value == other.value \
               and self.type_variable == other.type_variable

    def __str__(self):
        if self.type_variable == SpecialType.in_function:
            return "in[" + str(self.value) + "]"
        elif self.type_variable == SpecialType.out_function:
            return "out[" + str(self.value) + "]"
        else:
            return super(SpecialVariable, self).__str__()


class EqType(Enum):
    Term = 1
    Expr = 2


class Equation(object):

    def __init__(self, left_part, right_part, type_equation, func_name, index_sentence, sentence):
        self.left_part = left_part
        self.right_part = right_part
        self.type_equation = type_equation

        self.func_name = func_name
        self.index_sentence = index_sentence
        self.sentence = sentence

    def __eq__(self, other):
        return isinstance(other, Equation) \
               and self.left_part == other.left_part \
               and self.right_part == other.right_part \
               and self.type_equation == other.type_equation

    def __str__(self):
        return str(self.left_part) + " : " + str(self.right_part)

    def __hash__(self):
        return hash(self.__str__())


class Substitution(object):

    def __init__(self, left_part, right_part, alternative_right_part=None):
        self.left_part = left_part
        self.right_part = right_part

        self.alternative_right_part = alternative_right_part

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other, Substitution) \
               and self.left_part == other.left_part \
               and self.right_part == other.right_part

    def __str__(self):
        output_str = str(self.left_part) + " -> " + str(self.right_part)
        if self.alternative_right_part is not None:
            output_str += " | " + str(self.alternative_right_part)
        return output_str


class Assignment(object):

    def __init__(self, left_part, right_part):
        self.left_part = left_part
        self.right_part = right_part

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return isinstance(other, Assignment) \
               and self.left_part == other.left_part \
               and self.right_part == other.right_part

    def __str__(self):
        return str(self.left_part) + " <- " + str(self.right_part)


def make_alternative(substitutions):
    i = 0
    substitutions_result = []
    substitutions_variant = []
    while i < len(substitutions):
        j = 0
        while j < len(substitutions_variant):
            if substitutions_variant[j].left_part == substitutions[i].left_part:
                break
            j += 1
        if j == len(substitutions_variant):
            substitutions_variant.append(substitutions[i])
        else:
            substitutions_result.append(deepcopy(substitutions_variant))
            substitutions_variant = substitutions_variant[:j]
            i -= 1
        i += 1
    substitutions_result.append(substitutions_variant)
    return substitutions_result


def has_alternative(substitutions):
    for subst in substitutions:
        if subst.alternative_right_part is not None:
            return True
    return False


def get_alternative_substitution(substitutions):
    for subst in substitutions:
        if subst.alternative_right_part is not None:
            return subst
    return None


def get_substitution_function_format(ast):
    format_substitution_function = []

    for function in ast.functions:
        if isinstance(function, Definition):
            for sentence in function.sentences:
                if not sentence.no_substitution:
                    format_substitution_function.append(Substitution(
                        Expression([SpecialVariable(function.name, SpecialType.in_function)]),
                        sentence.pattern))

                    if not any(isinstance(term, SpecialVariable) and term.type_variable == SpecialType.out_function
                               for term in sentence.result.terms):
                        format_substitution_function.append(Substitution(
                            Expression([SpecialVariable(function.name, SpecialType.out_function)]),
                            sentence.result))

    return format_substitution_function


def has_repeated_variable(exprs):
    i, j = 0, 0
    while i < len(exprs.terms):
        while j < len(exprs.terms):
            if i == j:
                j += 1
                continue
            else:
                if isinstance(exprs.terms[i], Variable) and isinstance(exprs.terms[j], Variable) \
                        and exprs.terms[i] == exprs.terms[j]:
                    return True
                else:
                    j += 1
        i += 1
    return False


def delete_same_assignments(assignments, substitution):
    i, j = 0, 0
    while i < len(assignments):
        while j < len(substitution):

            if assignments[i].right_part == substitution[j].left_part:
                del assignments[i]
                i -= 1
                break

            j += 1
        i += 1

    return assignments, substitution


class Calculation(object):

    def __init__(self, ast, ast_type):
        self.ast = deepcopy(ast)
        self.ast_type = deepcopy(ast_type)

        self.block_to_condition()
        self.numerate_variable()

        if DEBUG_MODE:
            print(self.ast)
            print(LINE_DELIMITER)
            print(self.ast_type)

        self.default_format_function = self.prepare_default_format_function()
        self.format_function = []

        self.system_result = list(dict.fromkeys(self.create_equation_result()))
        self.system_condition_result, self.system_condition = self.create_equation_condition()

        if DEBUG_MODE:
            print(LINE_DELIMITER)
            for equation in self.system_result:
                print(equation)
            for equation in self.system_condition_result:
                print(equation)
            for equation in self.system_condition:
                print(equation)
            print(LINE_DELIMITER)

        self.error_messages = []

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

    def get_none(self, term):
        if isinstance(term, StructuralBrackets):
            for term in term.value:
                none_term = self.get_none(term)
                if none_term is not None:
                    return none_term
        elif isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none:
            return term
        elif isinstance(term, Expression):
            for term in term.terms:
                none_term = self.get_none(term)
                if none_term is not None:
                    return none_term
        else:
            return None

    def numerate_variable_function(self, exprs):
        variable_dict = dict()
        for term in exprs:
            variables = self.get_variables(term)
            for i in range(len(variables)):
                if variables[i].value not in variable_dict:
                    if variables[i].index >= 0:
                        variable_dict[variables[i].value] = generate_index()
                    else:
                        variable_dict[variables[i].value] = generate_built_in_index()
                variables[i] = change_variable_index(variables[i], variable_dict[variables[i].value])
        return exprs

    def numerate_variable(self):
        index = 0
        for function in self.ast.functions:
            if isinstance(function, Definition):
                self.numerate_variable_rec(function.sentences, index, dict())
        for function_type in self.ast_type.functions:
            if isinstance(function_type, DefinitionType):
                self.numerate_variable_built_in(function_type)

    def numerate_variable_rec(self, sentences, index, variable_dict):
        for sentence in sentences:
            index += 1
            for term in sentence.pattern.terms:
                variables = self.get_variables(term)
                for i in range(len(variables)):
                    if variables[i].value not in variable_dict:
                        variable_dict[variables[i].value] = generate_index()
                    variables[i] = change_variable_index_and_index_sentence(variables[i], variable_dict[variables[i].value], index)
            for condition in sentence.conditions:
                for term_condition in condition.pattern.terms:
                    variables = self.get_variables(term_condition)
                    for i in range(len(variables)):
                        if variables[i].value not in variable_dict:
                            variable_dict[variables[i].value] = generate_index()
                        variables[i] = change_variable_index_and_index_sentence(variables[i], variable_dict[variables[i].value],
                                                                                index)
                for term_result in condition.result.terms:
                    variables = self.get_variables(term_result)
                    for i in range(len(variables)):
                        if variables[i].value not in variable_dict:
                            variable_dict[variables[i].value] = generate_index()
                        variables[i] = change_variable_index_and_index_sentence(variables[i], variable_dict[variables[i].value],
                                                                                index)
            if sentence.block:
                self.numerate_variable_rec(sentence.block, 0, variable_dict)
            for term_result in sentence.result.terms:
                variables = self.get_variables(term_result)
                for i in range(len(variables)):
                    if variables[i].value not in variable_dict:
                        variable_dict[variables[i].value] = generate_index()
                    variables[i] = change_variable_index_and_index_sentence(variables[i], variable_dict[variables[i].value], index)

    def numerate_variable_built_in(self, function_type):
        for term in function_type.pattern.terms:
            variables = self.get_variables(term)
            for i in range(len(variables)):
                variables[i] = change_variable_index_and_index_sentence(variables[i], generate_built_in_index(), 0)
        for term in function_type.result.terms:
            variables = self.get_variables(term)
            for i in range(len(variables)):
                variables[i] = change_variable_index_and_index_sentence(variables[i], generate_built_in_index(), 0)

    def make_hard(self, expr):
        if len(expr.terms) == 0:
            return Expression([])
        elif is_symbol(expr.terms[0]):
            return Expression([expr.terms[0], *self.make_hard(Expression(expr.terms[1:])).terms])
        elif is_symbol(expr.terms[-1]):
            return Expression([*self.make_hard(Expression(expr.terms[:-1])).terms, expr.terms[-1]])
        elif isinstance(expr.terms[0], Variable) and (
                expr.terms[0].type_variable == Type.s or expr.terms[0].type_variable == Type.t):
            return Expression([expr.terms[0], *self.make_hard(Expression(expr.terms[1:])).terms])
        elif isinstance(expr.terms[-1], Variable) and \
                (expr.terms[-1].type_variable == Type.s or expr.terms[-1].type_variable == Type.t):
            return Expression([*self.make_hard(Expression(expr.terms[:-1])).terms, expr.terms[-1]])
        elif isinstance(expr.terms[0], StructuralBrackets):
            return Expression([StructuralBrackets(*self.make_hard(Expression(expr.terms[0].value)).terms),
                               *self.make_hard(Expression(expr.terms[1:])).terms])
        elif isinstance(expr.terms[-1], StructuralBrackets):
            return Expression([*self.make_hard(Expression(expr.terms[:-1])).terms,
                               StructuralBrackets(*self.make_hard(Expression(expr.terms[-1].value)).terms)])
        elif len(expr.terms) == 1 and isinstance(expr.terms[0], Variable) and expr.terms[0].type_variable == Type.e:
            return Expression([expr.terms[0]])
        elif len(expr.terms) == 1 and isinstance(expr.terms[0], SpecialVariable) \
                and expr.terms[0].type_variable == SpecialType.none:
            return Expression([expr.terms[0]])
        else:
            index = generate_index()
            e_variable = Variable("%d".format(index), Type.e, None, index)
            return Expression([e_variable])

    def prepare_default_format_function(self):

        format_function = []

        call_functions = []

        for function in self.ast.functions:
            if isinstance(function, Definition):
                for sentence in function.sentences:
                    for condition in sentence.conditions:
                        for term_result in condition.result.terms:
                            call_functions.extend(self.get_call(term_result))

                    for term_result in sentence.result.terms:
                        call_functions.extend(self.get_call(term_result))

        call_functions = list(set(call_functions))

        for definition_type_function in self.ast_type.functions:
            if isinstance(definition_type_function, DefinitionType):
                for call_function in call_functions:
                    if definition_type_function.name == call_function:
                        in_format = Expression(
                            [SpecialVariable(definition_type_function.name, SpecialType.in_function)])
                        out_format = Expression(
                            [SpecialVariable(definition_type_function.name, SpecialType.out_function)])
                        format_function.append(Substitution(in_format, definition_type_function.pattern))
                        format_function.append(Substitution(out_format, definition_type_function.result))

        return format_function

    def create_equation_condition(self):
        all_equations = []
        equations_conditions = []
        for function in self.ast.functions:
            if isinstance(function, Definition):
                equations = []
                for sentence in function.sentences:
                    for condition in sentence.conditions:
                        for i in range(len(condition.result.terms)):
                            if isinstance(condition.result.terms[i], CallBrackets):
                                sentence.has_call = True
                                equations_new, _1, _2 = self.replace_call(condition.result.terms[i].content,
                                                                          condition.result.terms[i].value,
                                                                          function.sentences.index(sentence),
                                                                          sentence)
                                equations.extend(equations_new)
                                condition.result.terms[i] = SpecialVariable(condition.result.terms[i].value,
                                                                            SpecialType.out_function)
                            elif isinstance(condition.result.terms[i], StructuralBrackets):
                                equations_new, _1, _2 = self.replace_call(condition.result.terms[i].value,
                                                                          None,
                                                                          function.sentences.index(sentence),
                                                                          sentence)
                                equations.extend(equations_new)

                        equations_conditions.append(Equation(condition.result, condition.pattern, EqType.Expr,
                                                             function.name, function.sentences.index(sentence),
                                                             sentence))
                all_equations.extend(equations)
        return all_equations, equations_conditions

    def create_equation_result(self):
        all_equations = []
        for function in self.ast.functions:
            if isinstance(function, Definition):
                equations = []
                for sentence in function.sentences:
                    for i in range(len(sentence.result.terms)):
                        if isinstance(sentence.result.terms[i], CallBrackets):
                            sentence.has_call = True
                            equations_new, _1, _2 = self.replace_call(sentence.result.terms[i].content,
                                                                      sentence.result.terms[i].value,
                                                                      function.sentences.index(sentence),
                                                                      sentence)
                            equations.extend(equations_new)
                            sentence.result.terms[i] = SpecialVariable(sentence.result.terms[i].value,
                                                                       SpecialType.out_function)
                        elif isinstance(sentence.result.terms[i], StructuralBrackets):
                            equations_new, _1, _2 = self.replace_call(sentence.result.terms[i].value,
                                                                      None,
                                                                      function.sentences.index(sentence),
                                                                      sentence)
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

    def block_to_condition(self):
        for function in self.ast.functions:
            if isinstance(function, Definition):
                for sentence in function.sentences:
                    if sentence.block:
                        function.sentences.remove(sentence)

                        for sentence_block in sentence.block:
                            sentence_copy = deepcopy(sentence)
                            sentence_copy.block = []

                            sentence_result = sentence_copy.result
                            sentence_copy.conditions.append(Condition(sentence_result, sentence_block.pattern))
                            sentence_copy.result = sentence_block.result

                            function.sentences.append(sentence_copy)

    def replace_call(self, terms, func_name, index_sentence, sentence):
        equations = []
        i = 0
        while i < len(terms):
            if isinstance(terms[i], CallBrackets):
                sentence.has_call = True
                equations_new, _, flag = self.replace_call(terms[i].content, terms[i].value,
                                                           index_sentence, sentence)
                terms[i] = SpecialVariable(terms[i].value, SpecialType.out_function)
                equations.extend(equations_new)
            elif isinstance(terms[i], StructuralBrackets):
                equations_new, terms_new, flag = self.replace_call(terms[i].value, None, index_sentence,
                                                                   sentence)
                terms[i] = StructuralBrackets(terms_new)
                if flag:
                    equations.extend(equations_new)
            i += 1
        if func_name is not None:
            in_variable = Expression([SpecialVariable(func_name, SpecialType.in_function)])
            return [Equation(Expression(terms), in_variable, EqType.Expr, func_name, index_sentence, sentence),
                    *equations], terms, True
        else:
            return [], terms, False

    def apply_substitution(self, expr, subst, flag=False):
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
                        if len(substitution.left_part.terms) == 1 and isinstance(substitution.left_part.terms[0],
                                                                                 SpecialVariable) and not flag:

                            res.extend(self.numerate_variable_function(
                                self.apply_substitution(substitution.right_part, subst, flag).terms
                            ))

                        else:
                            res.extend(self.apply_substitution(substitution.right_part, subst, flag).terms)
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
                    if substitution.left_part == exprs or \
                            (len(substitution.left_part.terms) == 1 and substitution.left_part.terms[0] == exprs.terms[
                                i]):
                        exists_substitution = True
                        if isinstance(substitution.left_part.terms[0], SpecialVariable):
                            res.extend(self.numerate_variable_function(
                                self.apply_substitution(substitution.right_part, subst, flag).terms
                            ))
                        else:
                            res.extend(self.apply_substitution(substitution.right_part, subst, flag).terms)
                if not exists_substitution:
                    res.append(exprs.terms[i])
            elif isinstance(exprs.terms[i], StructuralBrackets):
                res.extend([StructuralBrackets(self.apply_substitution(Expression(exprs.terms[i].value), subst, flag).terms)])
            else:
                res.append(exprs.terms[i])
            i += 1
        return Expression(res)

    def apply_assignment(self, expr, assignments):
        res = []
        i = 0
        exprs = deepcopy(expr)
        while i < len(exprs.terms):
            if isinstance(exprs.terms[i], Variable):
                exist_assignment = False
                for assign in assignments:
                    if len(assign.right_part.terms) == 1 and assign.right_part.terms[0] == exprs.terms[i]:
                        exist_assignment = True
                        res.extend(assign.left_part.terms)
                if not exist_assignment:
                    res.append(exprs.terms[i])
            elif isinstance(exprs.terms[i], StructuralBrackets):
                res.extend([StructuralBrackets(self.apply_assignment(Expression(exprs.terms[i].value), assignments)
                                               .terms)])
            else:
                res.append(exprs.terms[i])
            i += 1
        return Expression(res)

    def generalization_expression(self, format_substitution_function):
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
                                   if len(format_function.left_part.terms) > 0 and
                                   isinstance(format_function.left_part.terms[0], SpecialVariable) and
                                   format_function.left_part.terms[0].type_variable != SpecialType.none]
        return format_functions_result

    def calculate_equation(self, system, ast):
        substitutions = []
        assignments = []
        k = 0

        while k < len(system):
            eq = deepcopy(system[k])

            eq.left_part = self.apply_substitution(eq.left_part, [*substitutions, *self.format_function,
                                                                  *self.default_format_function])
            eq.right_part = self.apply_substitution(eq.right_part, [*substitutions, *self.format_function,
                                                                    *self.default_format_function])

            if not (len(eq.right_part.terms) > 0 and
                    any(isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none
                        for term in eq.right_part.terms)) \
                    and not (len(eq.left_part.terms) > 0 and
                             any(isinstance(term, SpecialVariable) and term.type_variable == SpecialType.none
                                 for term in eq.left_part.terms)):
                status, substitution, assignment, _, _ = self.match_equation(eq, substitutions, assignments,
                                                                             system)

                assignment, substitution = delete_same_assignments(assignment, substitution)

                if has_alternative(substitution):
                    status, substitution_result, assignments_result, k = self.calculate_alternative_system(system,
                                                                                                        substitution,
                                                                                                        assignment,
                                                                                                        system[k], k,
                                                                                                        ast)

                if status != "Failure":
                    substitution = [subst for subst in substitution if not subst.left_part == subst.right_part]
                    assignment = [assign for assign in assignment if not assign.left_part == assign.right_part]

                    for subst in substitution:
                        if subst not in substitutions:
                            substitutions.append(subst)

                    for assign in assignment:
                        if assign not in assignments:
                            assignments.append(assign)

                if status == "Failure":
                    error_message = "Function %s, sentence %d, there isn't solution for equation: %s" % (
                        system[k].func_name, system[k].index_sentence, self.print_equation(system[k]))

                    if not any(msg.startswith(error_message) for msg in self.error_messages):
                        substitution = self.apply_substitution(system[k].right_part,
                                                               [*substitution,
                                                                *substitutions,
                                                                *self.format_function,
                                                                *self.default_format_function])

                        error_message = error_message + " => " + self.print_expr(substitution) + "\n"
                        self.error_messages.append(error_message)

                    for function in ast.functions:
                        if isinstance(function, Definition):
                            for sentence in function.sentences:
                                if system[k].sentence == sentence:
                                    sentence.no_substitution = True

            else:
                substitution = [Substitution(eq.left_part, eq.right_part)]
                substitution = [subst for subst in substitution if not subst.left_part == subst.right_part]

                for subst in substitution:
                    if subst not in substitutions:
                        substitutions.append(subst)
            k += 1
        return substitutions, assignments

    def calculate_alternative_system(self, system, substitutions, assignments, equation, j, ast):
        substitution_alternative = get_alternative_substitution(substitutions)

        if DEBUG_MODE:
            print(LINE_DELIMITER)
            print(substitution_alternative)
            print(LINE_DELIMITER)

        substitutions.remove(substitution_alternative)

        substitution_first_variant = Substitution(substitution_alternative.left_part,
                                                  substitution_alternative.right_part)

        status_first, substitutions_first, assignments_first, index_first = self.calculate_alternative_system_rec(system,
                                                                                                     [
                                                                                                         substitution_first_variant,
                                                                                                         *substitutions],
                                                                                                     assignments, j,
                                                                                                     ast)

        substitution_second_variant = Substitution(substitution_alternative.left_part,
                                                   substitution_alternative.alternative_right_part)

        status_second, substitutions_second, assignments_second, index_second = self.calculate_alternative_system_rec(system,
                                                                                                        [
                                                                                                            substitution_second_variant,
                                                                                                            *substitutions],
                                                                                                        assignments, j,
                                                                                                        ast)
        index_result = None
        if status_first == "Success":
            for subst in substitutions_first:
                if subst not in substitutions:
                    substitutions.append(subst)
            if substitutions_first not in substitutions:
                substitutions.append(substitution_first_variant)

            for assign in assignments_first:
                if assign not in assignments:
                    assignments.append(assign)

            index_result = index_first

        if status_second == "Success":
            for subst in substitutions_second:
                if subst not in substitutions:
                    substitutions.append(subst)
            if substitutions_second not in substitutions:
                substitutions.append(substitution_second_variant)

            for assign in assignments_second:
                if assign not in assignments:
                    assignments.append(assign)

            index_result = index_second

        if status_first == "Failure" and status_second == "Failure":

            index_result = max(index_first, index_second)

            error_message = "Function %s, sentence %d, there isn't solution for equation: %s" % (
                system[index_result].func_name, system[index_result].index_sentence, self.print_equation(system[index_result]))

            if not any(msg.startswith(error_message) for msg in self.error_messages):
                substitution = self.apply_substitution(system[index_result].right_part,
                                                       [*substitutions,
                                                        *self.format_function,
                                                        *self.default_format_function])

                error_message = error_message + " => " + self.print_expr(substitution) + "\n"
                self.error_messages.append(error_message)

                for function in ast.functions:
                    if isinstance(function, Definition):
                        for sentence in function.sentences:
                            if system[j].sentence == sentence:
                                sentence.no_substitution = True

            return "Failure", [], [], index_result

        if DEBUG_MODE:
            print(LINE_DELIMITER)
            for subst in substitutions:
                print(subst)
            for assign in assignments:
                print(assign)
            print(LINE_DELIMITER)

        return "Success", list(dict.fromkeys(substitutions)), list(dict.fromkeys(assignments)), index_result

    def calculate_alternative_system_rec(self, system, substitutions, assignments, j, ast):
        substitutions_copy = deepcopy(substitutions)
        assignments_copy = deepcopy(assignments)

        is_first = True
        while j < len(system):
            eq = deepcopy(system[j])
            eq.left_part = self.apply_substitution(eq.left_part, [*substitutions_copy,
                                                                  *self.format_function,
                                                                  *self.default_format_function
                                                                  ], is_first)
            eq.right_part = self.apply_substitution(eq.right_part,
                                                    [*substitutions_copy,
                                                     *self.format_function,
                                                     *self.default_format_function
                                                     ], is_first)

            status, substitution_result, assignments_result, _, _ = self.match_equation(eq, substitutions_copy,
                                                                                        assignments_copy,
                                                                                        self.system_result)

            assignments_result, substitution_result = delete_same_assignments(assignments_result, substitution_result)

            if status == "Failure":
                return status, [], [], j

            if has_alternative(substitution_result):
                substitution_all = []
                for subst in substitution_result:
                    if subst not in substitution_all:
                        substitution_all.append(subst)

                for subst in substitutions_copy:
                    if subst not in substitution_all:
                        substitution_all.append(subst)

                assignments_all = []
                for assign in assignments_result:
                    if assign not in assignments_all:
                        assignments_all.append(assign)

                for assign in assignments_copy:
                    if assign not in assignments_all:
                        assignments_all.append(assign)

                status, substitution_alternative, assignments_alternative, index = \
                    self.calculate_alternative_system(system, substitution_all, assignments_all, system[j],
                                                      j, ast)

                if status == "Failure":
                    return status, [], [], index

                for subst in substitution_alternative:
                    if subst not in substitutions_copy:
                        substitutions_copy.append(subst)

                for assign in assignments_alternative:
                    if assign not in assignments_copy:
                        assignments_copy.append(assign)

                j = index
            else:
                substitution_result = [subst for subst in substitution_result if
                                       not subst.left_part == subst.right_part]

                assignments_result = [assign for assign in assignments_result if
                                      not assign.left_part == assign.right_part]

                for subst in substitution_result:
                    if subst not in substitutions_copy:
                        substitutions_copy.append(subst)

                for assign in assignments_result:
                    if assign not in assignments_copy:
                        assignments_copy.append(assign)

            j += 1
            is_first = False

        return "Success", substitutions_copy, assignments_copy, j

    def calculate_system(self):
        while True:
            substitutions = []
            assignments = []

            ast = deepcopy(self.ast)

            if len(self.system_condition_result) > 0:
                substitutions_condition, assignments_condition = self.calculate_equation(self.system_condition_result,
                                                                                         ast)

                substitutions_variant = make_alternative(substitutions_condition)
                for substitution_var in substitutions_variant:
                    substitution_var.extend(substitutions)

                substitutions = substitutions_variant

                assignments.extend(assignments_condition)

                for function in ast.functions:
                    if isinstance(function, Definition):
                        sentence_result = []
                        while len(function.sentences) > 0:
                            j = 0
                            if len(substitutions) > 0:
                                new_sentence = deepcopy(function.sentences[0])
                                del function.sentences[0]
                                while j < len(substitutions):

                                    sentence_copy = deepcopy(new_sentence)

                                    for condition in sentence_copy.conditions:
                                        condition.pattern = self.apply_substitution(condition.pattern,
                                                                                    [*substitutions[j],
                                                                                     *self.format_function,
                                                                                     *self.default_format_function])
                                        condition.pattern = self.make_hard(
                                            self.apply_assignment(condition.pattern, assignments))

                                        condition.result = self.apply_substitution(condition.result,
                                                                                   [*substitutions[j],
                                                                                    *self.format_function,
                                                                                    *self.default_format_function])
                                        condition.result = self.apply_assignment(condition.result, assignments)

                                    sentence_copy.pattern = self.apply_substitution(sentence_copy.pattern,
                                                                                    [*substitutions[j],
                                                                                     *self.format_function,
                                                                                     *self.default_format_function])
                                    sentence_copy.pattern = self.apply_assignment(sentence_copy.pattern,
                                                                                  assignments)

                                    sentence_copy.result = self.apply_substitution(sentence_copy.result,
                                                                                   [*substitutions[j],
                                                                                    *self.format_function,
                                                                                    *self.default_format_function])
                                    sentence_copy.result = self.apply_assignment(sentence_copy.result,
                                                                                 assignments)
                                    if sentence_copy not in sentence_result:
                                        sentence_result.append(sentence_copy)

                                    j += 1

                        function.sentences.extend(sentence_result)

                self.system_condition = []
                for function in ast.functions:
                    if isinstance(function, Definition):
                        for sentence in function.sentences:
                            for condition in sentence.conditions:
                                if not has_repeated_variable(condition.result):
                                    eq = Equation(condition.result, condition.pattern, EqType.Expr,
                                                  function.name, function.sentences.index(sentence),
                                                  sentence)
                                    self.system_condition.append(eq)

                substitutions_condition, assignments_condition = self.calculate_equation(
                    self.system_condition, ast)
                substitutions_variant = make_alternative(substitutions_condition)
                for substitution_var in substitutions_variant:
                    for subst in substitutions:
                        substitution_var.extend(subst)

                substitutions = substitutions_variant

                assignments.extend(assignments_condition)

            if len(self.system_result) == 0:
                for function in ast.functions:
                    if isinstance(function, Definition):
                        sentence_result = []
                        while len(function.sentences) > 0:
                            i = 0
                            new_sentence = deepcopy(function.sentences[0])
                            del function.sentences[0]
                            if len(substitutions) > 0:
                                while i < len(substitutions):

                                    sentence_first = deepcopy(new_sentence)

                                    sentence_first.pattern = self.apply_substitution(sentence_first.pattern,
                                                                                     [*substitutions[i],
                                                                                      *self.format_function,
                                                                                      *self.default_format_function])
                                    sentence_first.pattern = self.apply_assignment(sentence_first.pattern, assignments)

                                    sentence_first.result = self.apply_substitution(sentence_first.result,
                                                                                    [*substitutions[i],
                                                                                     *self.format_function,
                                                                                     *self.default_format_function])
                                    sentence_first.result = self.apply_assignment(sentence_first.result, assignments)

                                    if sentence_first not in sentence_result:
                                        sentence_result.append(sentence_first)
                                    i += 1
                            else:
                                if new_sentence not in sentence_result:
                                    sentence_result.append(new_sentence)

                        function.sentences.extend(sentence_result)

                format_substitution_function = get_substitution_function_format(ast)
                format_functions_result = self.generalization_expression(format_substitution_function)

                if self.is_fixed_point(self.format_function, format_functions_result):
                    break
                else:
                    self.format_function = format_functions_result

                    if DEBUG_MODE:
                        print(LINE_DELIMITER)
                        for assignment in assignments:
                            print(assignment)
                        for substitution_variant in substitutions:
                            print(', '.join(map(str, substitution_variant)))
                        for format_function in self.format_function:
                            print(format_function)
                        print(LINE_DELIMITER)
            else:
                for function in ast.functions:
                    if isinstance(function, Definition):
                        sentence_result = []
                        while len(function.sentences) > 0:
                            i = 0
                            new_sentence = deepcopy(function.sentences[0])
                            del function.sentences[0]
                            if len(substitutions) > 0:
                                while i < len(substitutions):

                                    sentence_first = deepcopy(new_sentence)

                                    sentence_first.pattern = self.apply_substitution(sentence_first.pattern,
                                                                                     [*substitutions[i],
                                                                                      *self.format_function,
                                                                                      *self.default_format_function])
                                    sentence_first.pattern = self.apply_assignment(sentence_first.pattern, assignments)

                                    sentence_first.result = self.apply_substitution(sentence_first.result,
                                                                                    [*substitutions[i],
                                                                                     *self.format_function,
                                                                                     *self.default_format_function])
                                    sentence_first.result = self.apply_assignment(sentence_first.result, assignments)

                                    if sentence_first not in sentence_result:
                                        sentence_result.append(sentence_first)
                                    i += 1
                            else:
                                if new_sentence not in sentence_result:
                                    sentence_result.append(new_sentence)

                        function.sentences.extend(sentence_result)

                for eq in self.system_result:
                    eq.sentence.no_substitution = False

                    # eq.left_part = self.apply_substitution(eq.left_part,
                    #                                        [*self.format_function, *self.default_format_function])
                    # eq.right_part = self.apply_substitution(eq.right_part,
                    #                                         [*self.format_function, *self.default_format_function])

                substitutions_result, assignments_result = self.calculate_equation(
                    self.system_result, ast)

                substitutions_variant = make_alternative(substitutions_result)
                for substitution_var in substitutions_variant:
                    for subst in substitutions:
                        substitution_var.extend(subst)

                assignments.extend(assignments_result)

                substitutions = substitutions_variant

                for function in ast.functions:
                    if isinstance(function, Definition):
                        sentence_result = []
                        while len(function.sentences) > 0:
                            i = 0
                            if len(substitutions) > 0:
                                sentence_copy = deepcopy(function.sentences[0])
                                del function.sentences[0]
                                while i < len(substitutions):
                                    new_sentence = deepcopy(sentence_copy)

                                    if sentence_copy.has_call:

                                        new_sentence.pattern = self.apply_substitution(new_sentence.pattern,
                                                                                       [*substitutions[i],
                                                                                        *self.format_function,
                                                                                        *self.default_format_function])
                                        new_sentence.pattern = self.apply_assignment(new_sentence.pattern, assignments)

                                        new_sentence.result = self.apply_substitution(new_sentence.result,
                                                                                      [*substitutions[i],
                                                                                       *self.format_function,
                                                                                       *self.default_format_function])
                                        new_sentence.result = self.apply_assignment(new_sentence.result, assignments)

                                        if new_sentence not in sentence_result:
                                            sentence_result.append(new_sentence)
                                    else:
                                        if new_sentence not in sentence_result:
                                            sentence_result.append(new_sentence)

                                    i += 1

                        function.sentences.extend(sentence_result)

                format_substitution_function = get_substitution_function_format(ast)
                format_functions_result = self.generalization_expression(format_substitution_function)

                if self.is_fixed_point(self.format_function, format_functions_result):
                    break
                else:
                    self.format_function = format_functions_result

                    if DEBUG_MODE:
                        print(LINE_DELIMITER)
                        for assignment in assignments:
                            print(assignment)
                        for substitution in substitutions:
                            print(', '.join(map(str, substitution)))
                        for format_function in self.format_function:
                            print(format_function)
                        print(LINE_DELIMITER)

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
                            Substitution(key_group, Expression(common_format[key_group][1].terms[i].value))]

                        if not self.is_fixed_point(before_common_format_brackets, after_common_format_brackets):
                            return False

                    elif not (isinstance(common_format[key_group][0].terms[i], Variable) and
                              isinstance(common_format[key_group][1].terms[i], Variable) and
                              common_format[key_group][0].terms[i].type_variable == common_format[key_group][1].terms[
                                  i].type_variable) and \
                            not common_format[key_group][0].terms[i] == common_format[key_group][1].terms[i]:
                        return False

        return True

    def match_equation(self, equation, substitution, assignments, system):
        eq = deepcopy(equation)
        if eq.left_part.terms == [] and eq.right_part.terms == []:
            return "Success", substitution, assignments, system, eq
        else:
            if eq.type_equation == EqType.Term:
                term_left = eq.left_part.terms[0]
                term_right = eq.right_part.terms[0]

                if isinstance(term_right, Variable) and isinstance(term_left, Variable) and term_left == term_right:
                    return "Success", substitution, assignments, system, eq
                if is_symbol(term_left) and is_symbol(term_right) and term_left == term_right:
                    return "Success", substitution, assignments, system, eq
                elif (isinstance(term_right, Variable) and term_right.type_variable == Type.t) and \
                        ((isinstance(term_left, Variable) and
                          (term_left.type_variable == Type.s or term_left.type_variable == Type.t))
                         or isinstance(term_left, StructuralBrackets) or is_symbol(term_left)):
                    assignments.append(Assignment(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, assignments, system, eq
                elif ((isinstance(term_right, Variable) and term_right.type_variable == Type.s) or is_symbol(
                        term_right)) \
                        and isinstance(term_left, Variable) and term_left.type_variable == Type.t:
                    substitution.append(Substitution(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, assignments, system, eq
                elif (isinstance(term_right, Variable) and term_right.type_variable == Type.s) and \
                        ((isinstance(term_left, Variable) and term_left.type_variable == Type.s) or is_symbol(
                            term_left)):
                    assignments.append(Assignment(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, assignments, system, eq
                elif (isinstance(term_left, Variable) and term_left.type_variable == Type.s) and is_symbol(
                        term_right):
                    if term_left.index > 0:
                        substitution.append(Substitution(Expression([term_left]), Expression([term_right])))
                    return "Success", substitution, assignments, system, eq
                elif isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
                    eq.type_equation = EqType.Expr
                    eq.left_part.terms = Expression(term_left.value).terms
                    eq.right_part.terms = Expression(term_right.value).terms
                    return self.match_equation(eq, substitution, assignments, system)
                elif isinstance(term_right, StructuralBrackets) and isinstance(term_left, Variable) \
                        and term_left.type_variable == Type.t:
                    index = generate_index()
                    e_variable = Variable("generated%d".format(index), Type.e, None, index)
                    substitution.append(Substitution(Expression([term_left]),
                                                     Expression([StructuralBrackets([e_variable])])))

                    eq.type_equation = EqType.Expr
                    eq.left_part.terms = Expression([e_variable]).terms
                    eq.right_part.terms = Expression(term_right.value).terms
                    return self.match_equation(eq, substitution, assignments, system)
                else:
                    return "Failure", [], [], system, eq

            else:
                if len(eq.left_part.terms) > 0 and is_hard_term(eq.left_part.terms[0]) \
                        and len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[0]):

                    subst = deepcopy(substitution)
                    assign = deepcopy(assignments)
                    syst = deepcopy(system)

                    status, subst, assign, syst, e = self.match_equation(
                        Equation(Expression([eq.left_part.terms[0]]),
                                 Expression([eq.right_part.terms[0]]),
                                 EqType.Term, eq.func_name,
                                 eq.index_sentence, eq.sentence), subst,
                        assign, syst)

                    eq.left_part.terms = eq.left_part.terms[1:]
                    eq.right_part.terms = eq.right_part.terms[1:]

                    if status == "Success":
                        substitution = subst
                        system = syst
                        assignments = assign
                        return self.match_equation(eq, substitution, assignments, system)
                    else:
                        return "Failure", substitution, assignments, system, eq

                elif len(eq.left_part.terms) > 0 and is_hard_term(eq.left_part.terms[-1]) \
                        and len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[-1]):

                    subst = deepcopy(substitution)
                    assign = deepcopy(assignments)
                    syst = deepcopy(system)

                    status, subst, assign, syst, e = self.match_equation(
                        Equation(Expression([eq.left_part.terms[-1]]),
                                 Expression([eq.right_part.terms[-1]]),
                                 EqType.Term, eq.func_name,
                                 eq.index_sentence, eq.sentence), subst,
                        assign, syst)

                    eq.left_part.terms = eq.left_part.terms[:-1]
                    eq.right_part.terms = eq.right_part.terms[:-1]

                    if status == "Success":
                        substitution = subst
                        assignments = assign
                        system = syst
                        return self.match_equation(eq, substitution, assignments, system)
                    else:
                        return "Failure", substitution, assignments, system, eq

                if len(eq.left_part.terms) > 0 and isinstance(eq.left_part.terms[0], Variable) and \
                        eq.left_part.terms[0].type_variable == Type.e and len(eq.right_part.terms) > 0 \
                        and is_hard_term(eq.right_part.terms[0]):
                    index = generate_index()
                    t_variable = Variable("generated%d".format(index), Type.t, None, index)
                    index = generate_index()
                    e_variable = Variable("generated%d".format(index), Type.e, None, index)
                    substitution_result = [*substitution,
                                           Substitution(Expression([eq.left_part.terms[0]]), Expression([]),
                                                        Expression([t_variable, e_variable]))]

                    return "Success", substitution_result, assignments, system, eq

                if len(eq.left_part.terms) > 0 and isinstance(eq.left_part.terms[-1], Variable) and \
                        eq.left_part.terms[-1].type_variable == Type.e and len(eq.right_part.terms) > 0 \
                        and is_hard_term(eq.right_part.terms[-1]):
                    index = generate_index()
                    e_variable = Variable("generated%d".format(index), Type.e, None, index)
                    index = generate_index()
                    t_variable = Variable("generated%d".format(index), Type.t, None, index)
                    substitution_result = [*substitution,
                                           Substitution(Expression([eq.left_part.terms[-1]]), Expression([]),
                                                        Expression([e_variable, t_variable]))]

                    return "Success", substitution_result, assignments, system, eq

                if len(eq.left_part.terms) == 0:

                    if len(eq.right_part.terms) > 0 and is_hard_term(eq.right_part.terms[0]):
                        return "Failure", [], [], system, eq

                    if len(eq.right_part.terms) == 0:
                        return "Success", substitution, assignments, system, eq

                    if all(isinstance(term, Variable) and term.type_variable == Type.e for term in
                           eq.right_part.terms):
                        for term in eq.left_part.terms:
                            assignments.append(Assignment(Expression([]), Expression([term])))
                        return "Success", substitution, assignments, system, eq

                    return "Undefined", [], [], system, eq

                if len(eq.right_part.terms) == 0:
                    if all(isinstance(term, Variable) and term.type_variable == Type.e for term in
                           eq.left_part.terms):
                        for term in eq.left_part.terms:
                            substitution.append(Substitution(Expression([term]), Expression([])))
                        return "Success", substitution, assignments, system, eq
                    else:
                        return "Failure", [], [], system, eq

                if len(eq.right_part.terms) == 1:
                    if isinstance(eq.right_part.terms[0], Variable) and eq.right_part.terms[0].type_variable == Type.e:
                        assignments.append(
                            Assignment(Expression(eq.left_part.terms), Expression([eq.right_part.terms[0]])))
                        return "Success", substitution, assignments, system, eq
                    else:
                        return "Failure", [], [], system, eq

                else:
                    return "Undefined", [], [], system, eq

    def generalization_term_rec(self, term_left, term_right):
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
            if term_left == term_right:
                return term_left
            else:
                index = generate_index()
                return Variable("generated%d".format(index), Type.s, None, index)
        if isinstance(term_left, Variable) and term_left.type_variable == Type.t:
            return term_left
        if isinstance(term_right, Variable) and term_right.type_variable == Type.t:
            return term_right
        if isinstance(term_left, StructuralBrackets) and isinstance(term_right, StructuralBrackets):
            result_terms = self.generalization([Expression(term_left.value), Expression(term_right.value)]).terms
            return StructuralBrackets(result_terms)
        if isinstance(term_left, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.t, None, index)
        if isinstance(term_right, StructuralBrackets):
            index = generate_index()
            return Variable("generated%d".format(index), Type.t, None, index)

    def generalization_term(self, terms):
        terms_copy = deepcopy(terms)
        if len(terms_copy) > 1:
            while len(terms_copy) > 1:
                term = self.generalization_term_rec(terms_copy.pop(), terms_copy.pop())
                terms_copy.append(term)
            return terms_copy[0]
        else:
            term = terms_copy.pop()
            result_term = self.generalization_term_rec(term, deepcopy(term))
            return result_term

    def generalization(self, patterns):
        if len(patterns) > 1:
            for pattern in patterns:
                special_value = self.get_none(pattern)
                if special_value is not None:
                    patterns.remove(pattern)
                    return self.generalization(patterns)
        elif len(patterns) == 1:
            special_value = self.get_none(patterns[0])
            if special_value is not None:
                return Expression([special_value])

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
                    if left == right and len(left) == 1:
                        return Expression(left)
                    else:
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

    def print_format_function(self):
        for error_message in self.error_messages:
            sys.stderr.write(error_message)

        result_str = "/* result program refalcheck */\n\n"

        for format_function in self.format_function:
            format_function.right_part.terms = append_char_term(format_function.right_part.terms)

        for function in self.ast.functions:
            if isinstance(function, Definition):
                in_format = Expression([SpecialVariable(function.name, SpecialType.in_function)])
                out_format = Expression([SpecialVariable(function.name, SpecialType.out_function)])
                if function.is_entry:
                    result_str = result_str + function.name + " "
                else:
                    result_str = result_str + "*" + function.name + " "
                for format_function in self.format_function:
                    if format_function.left_part == in_format:
                        pattern = format_function.right_part
                        result_str += (' '.join(list(map(self.print_term, pattern.terms))) + ' ')
                    if format_function.left_part == out_format:
                        result_str += ("=" + ' ')
                        result = format_function.right_part
                        result_str += (' '.join(list(map(self.print_term, result.terms))) + '')
                result_str += "\n"

        return result_str

    def print_expr(self, expr):
        return ' '.join(list(map(self.print_term, expr.terms)))

    def print_equation(self, equation):
        result_str = ""
        result_str += (' '.join(list(map(self.print_term, equation.left_part.terms))))
        result_str += " : "
        result_str += (' '.join(list(map(self.print_term, equation.right_part.terms))))
        return result_str

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
