#! python -v
# -*- coding: utf-8 -*-


def generate_index():
    generate_index.counter += 1
    return generate_index.counter


generate_index.counter = -1


def generate_built_in_index():
    generate_built_in_index.counter -= 1
    return generate_built_in_index.counter


generate_built_in_index.counter = 0
