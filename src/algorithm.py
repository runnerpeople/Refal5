#! python -v
# -*- coding: utf-8 -*-

from src.tokens import *
# from src.variable import *

# def replace_call(sentence):
#     for term in sentence:
#         # equation =
#
#
# def prepare_func(dict_func):
#     # index = 0
#     for key_func in dict_func.keys():
#         for sentence in dict_func[key_func]:
#             system = replace_call(sentence)
#
#
# def calculate_type(dict_func):
#     system_equation = prepare_func(dict_func)
#
#
#
#
# def convert_to_variable(term):
#     convert_term = []
#     for t in term:
#         if t.tag == DomainTag.Variable and t.value[0] == "s":
#             convert_term.append(SVar(t.value[2:]))
#         elif t.tag == DomainTag.Variable and t.value[0] == "t":
#             convert_term.append(TVar(t.value[2:]))
#         elif t.tag == DomainTag.Variable and t.value[0] == "e":
#             convert_term.append(EVar(t.value[2:]))
#         elif t.tag == DomainTag.Ident or t.tag == DomainTag.Number or t.tag == DomainTag.Characters:
#             if t.tag == DomainTag.Left_bracket:
#                 convert_term.append(SymbolVar(t.value[1:]))
#             else:
#                 convert_term.append(SymbolVar(t.value))
#     return convert_term
#
#
# def generate():
#     generate.counter += 1
#     return generate.counter
#
#
# generate.counter = 0
#
#
# def local_gen(num, term_left, term_right):
#     return local_gen_rec([term_left, term_left[num:]], [term_right])
#
#
# def local_gen_rec(term_left, term_right):
#     if not term_left[0]:
#         local_gen_term = [term_left[0], EVar(generate()), term_right[0][-1]]
#         return calc_complexity(local_gen_term)
#     else:
#
#         term_left_next = term_left[0][0]
#         term_right_next = term_right[0][-1]
#
#         local = [term_left[0], EVar(generate()), term_right[0][-1], term_right[0][-2::-1]]
#
#         result = calc_complexity(local)
#
#         result.append(local_gen_rec([*term_left[0], term_left_next], term_right[0][-2::-1]))
#
#
# def calc_complexity(term):
#     complexity = 0
#     for t in term:
#         if t.type_variable == Type.s:
#             complexity += 2
#         elif t.type_variable == Type.t:
#             complexity += 1
#         elif t.type_variable == Type.e:
#             complexity -= 1
#         elif t.type_variable == Type.symbol:
#             complexity += 3
#         elif t.type_variable == Type.symbol:
#             complexity += 2
#     return complexity + 1
