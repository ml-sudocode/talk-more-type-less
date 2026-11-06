import ast
from pathlib import Path
import re
source = (Path(__file__).resolve().parents[1] / 'app/dictation.py').read_text()
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'apply_spoken_punctuation')
ns = {'re': re}
exec(compile(ast.Module(body=[function], type_ignores=[]), '<test>', 'exec'), ns)
cases = {
    'Hello comma world period': 'Hello, world.',
    'Is this working question mark': 'Is this working?',
    'Hello, comma, world. Period.': 'Hello, world.',
    'Really. Question mark.': 'Really?',
    'Yes EXCLAMATION POINT': 'Yes!',
    'One colon two semicolon three full stop': 'One: two; three.',
    'First period new paragraph Second period': 'First.\n\nSecond.',
    'One new line two': 'One\ntwo',
    'The periodic table and commas remain.': 'The periodic table and commas remain.',
    'Already punctuated, as usual.': 'Already punctuated, as usual.',
    '': '',
    'and slash or': 'and/or',
    'A right arrow B left arrow C': 'A → B ← C',
    'Wait dash listen period': 'Wait — listen.',
    'Say open quote hello close quote period': 'Say “hello”.',
    'open quote hello comma world close quote': '“hello, world”',
    'open quote hello close quote right arrow next': '“hello” → next',
    'Go RIGHT ARROW home': 'Go → home',
}
for text, expected in cases.items():
    actual = ns['apply_spoken_punctuation'](text)
    assert actual == expected, (text, actual, expected)
print(f'PASS: {len(cases)} spoken punctuation cases; module compiles')
