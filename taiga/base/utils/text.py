# -*- coding: utf-8 -*-
def strip_lines(text):
    """
    Given text, try remove unnecessary spaces and
    put text in one unique line.
    """
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").strip()


def split_in_lines(text):
    """Split a block of text in lines removing unnecessary spaces from each line."""
    return (line for line in map(str.strip, text.split("\n")) if line)
