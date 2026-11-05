# Regex Engine From Scratch

A regular-expression engine written in pure Python, from scratch. It implements the classic compiler pipeline:

```
regex string ──parse──▶ AST ──Thompson──▶ ε-NFA ──subset construction──▶ DFA ──Hopcroft──▶ minimal DFA
```

## Example

```python
from src.Regex import parse_regex

nfa = parse_regex(r'[0-9]+((\+|-)[0-9]+)*').thompson()   # 20 states
dfa = nfa.subset_construction()                            #  8 states
min_dfa = dfa.minimize()                                   #  3 states

min_dfa.accept('12+3-45')   # True
min_dfa.accept('12+')       # False
```

## Supported syntax

| Syntax | Meaning |
|--------|---------|
| `ab` | concatenation |
| `a\|b` | alternation |
| `a*`, `a+`, `a?` | zero or more, one or more, optional |
| `( … )` | grouping |
| `[abc]`, `[a-z0-9]` | character classes and ranges |
| `\n`, `\t`, `\*`, `\ ` … | escapes (special characters, whitespace, literal space) |

Unescaped spaces are ignored.

## Implementation

### Parser: `src/Regex.py`
A **recursive descent parser** with one function per precedence level:

```
union   := concat ('|' concat)*
concat  := repeat+                  (implicit concatenation)
repeat  := atom ('*' | '+' | '?')*
atom    := char | '\' char | '[' class ']' | '(' union ')'
```

It produces an AST of `Char`, `CharClass`, `Concat`, `Union`, `Star`, `Plus` and `Optional` nodes.

### Thompson's construction: `src/Regex.py`
Each AST node builds its ε-NFA fragment recursively. `Plus` and `Optional` are expressed through the core constructions (`e+ = e·e*`, `e? = e|ε`).

### Subset construction: `src/NFA.py`
- `epsilon_closure` computes the states reachable through ε-transitions.
- `subset_construction` turns the ε-NFA into a DFA whose states are `frozenset`s of NFA states.

### Minimization: `src/DFA.py`
**Hopcroft's algorithm.** It starts from the partition {final, non-final} and keeps splitting blocks by their predecessors on each symbol, until no block can be refined further.

All automaton classes are generic over their state type, using the PEP 695 syntax `class DFA[STATE]`. `remap_states` converts between state types, for example `frozenset` to `int`.

## Running the tests

Requires **Python 3.12+**.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q test
```

There are 62 tests, all passing:
- `test/test_hw_1.py` covers ε-closure, subset construction and DFA minimization against the reference automata in `tests_1/`.
- `test/test_hw_2.py` covers regex → DFA end to end. Each result is checked for language equivalence against reference DFAs in `tests_2/`, including large ones of up to 12 MB.

## Repository layout

```
src/Regex.py    parser + Thompson construction
src/NFA.py      ε-closure, subset construction
src/DFA.py      acceptance, Hopcroft minimization
test/           pytest suites
tests_1/        reference automata for NFA → DFA and minimization
tests_2/        reference DFAs for regex → DFA
```

## Credits

Developed as a project for the *Formal Languages and Automata* course at the Faculty of Automatic Control and Computers, Politehnica University of Bucharest (2025). The course team provided the class skeletons and the test suites. The parser, the Thompson construction, the subset construction and the minimization are my own work.

## My Changes in This Fork

Forked by Muhammad Ahmad Farooq from [NaxonRO/Regex-Engine-From-Scratch](https://github.com/NaxonRO/Regex-Engine-From-Scratch) (MIT). The original project — a regex engine built from scratch in pure Python (parser, Thompson NFA, subset construction, Hopcroft DFA minimization) — is by NaxonRO; all credit for it belongs to the original author.

My change: the DFA can now search, not just match whole strings. I added a `search(text)` method to `src/DFA.py` that returns True when the pattern matches anywhere inside the text (like Python's `re.search`), while `accept()` still checks the whole string exactly as before. It walks the DFA from each start position using the same transition table as `accept()`, and handles the `None` destinations that `minimize()` writes for undefined transitions.

I added `test/test_search.py` with 10 tests (match in the middle, at the start, at the end, no match, the minimized DFA, and an `accept()` regression check). The full test suite — the repo's own 62 tests plus these 10 — passes: 72 in total.

What I learned: how a DFA runs step by step through its states, how Thompson construction and subset construction turn a regex into that DFA, and why a minimized DFA accepts the same language with fewer states.
