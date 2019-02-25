#! python -v
# -*- coding: utf-8 -*-


class Fragment(object):

    def __init__(self, starting, following):
        self.starting = starting
        self.following = following

    def __str__(self):
        return str(self.starting) + "-" + str(self.following)


class Position(object):

    def __init__(self, text, line=1, pos=1, index=0):
        self.text = text
        self.line = line
        self.pos = pos
        self.index = index

    def __eq__(self, other):
        return self.index == other.index

    def __lt__(self, other):
        return self.index < other.index

    def __str__(self):
        return "(" + str(self.line) + "," + str(self.pos) + ")"

    def is_eof(self):
        return self.index == len(self.text)

    def cp(self):
        return -1 if self.index == len(self.text) else ord(self.text[self.index])

    def letter(self):
        return "" if self.index >= len(self.text) else self.text[self.index]

    def read(self, n):
        cur = Position(self.text, self.line, self.pos, self.index)
        result_str = ""
        for i in range(0, n):
            if cur is not None:
                result_str += cur.letter()
                cur = next(cur, None)
        return result_str

    def __iter__(self):
        return self

    def is_white_space(self):
        return self.index != len(self.text) and self.letter().isspace()

    def is_letter(self):
        return self.index != len(self.text) and self.letter().isalpha()

    def is_digit(self):
        return self.index != len(self.text) and self.letter().isdigit()

    def is_letter_or_digit(self):
        return self.index != len(self.text) and self.letter().isalnum()

    def is_decimal_digit(self):
        return self.index != len(self.text) and "0" <= self.text[self.index] <= "9"

    def is_latin_letter(self):
        return self.index != len(self.text) and ("a" <= self.text[self.index] <= "z" or
                                                 "A" <= self.text[self.index] <= "Z")

    def is_new_line(self):
        if self.index == len(self.text):
            return True
        if self.text[self.index] == "\r" and self.index + 1 < len(self.text):
            return self.text[self.index+1] == "\n"
        return self.text[self.index] == "\n"

    def __next__(self):
        if not self.has_next():
            raise StopIteration
        elif self.is_new_line():
            if self.text[self.index] == "\r":
                self.index += 1
            self.line += 1
            self.pos = 1
        else:
            self.pos += 1
        self.index += 1
        return self

    def has_next(self):
        return self.index < len(self.text)
