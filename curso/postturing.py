import re
from typing import Iterable, NamedTuple

from .turing import *


class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int


def tokenize(code: str) -> Iterable[Token]:
    keywords = {'PRINT', 'IF', 'GOTO', 'RIGHT', 'LEFT'}
    token_specification = {
        'ID': r'[_a-zA-Z][a-zA-Z_0-9]*',
        'LABEL': r':',
        'SYMBOL': r"'.'",
        'NEWLINE': r'\n',
        'SKIP': r'[ \t]+',
        'MISMATCH': r'.+'
    }
    tok_regex = '|'.join(
        f'(?P<{key}>{value})'
        for key, value in token_specification.items())
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
        elif kind == 'ID' and value in keywords:
            kind = value
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} unexpected on line {line_num}')
        yield Token(kind, value, line_num, column)
