"""Tests for the proposed DFA.search() — unittest style, matching the repo's
own test files (test/test_hw_2.py uses unittest.TestCase).

The DFAs are built directly with the DFA constructor, using the exact field
layout from upstream src/DFA.py (S, K, q0, d, F). No parse_regex / NFA needed,
so these tests run without the rest of the repo.
"""
import unittest

from src.DFA import DFA

DIGITS = set("0123456789")


def digits_dfa():
    """DFA for [0-9]+ : one digit, then more digits. States: 0 start, 1 final."""
    d = {}
    for ch in DIGITS:
        d[(0, ch)] = 1
        d[(1, ch)] = 1
    return DFA(DIGITS, {0, 1}, 0, d, {1})


def arithmetic_dfa():
    """DFA for the README example [0-9]+((\\+|-)[0-9]+)* .
    States: 0 start, 1 = inside digits (final), 2 = just saw + or -."""
    d = {}
    for ch in DIGITS:
        d[(0, ch)] = 1
        d[(1, ch)] = 1
        d[(2, ch)] = 1
    d[(1, "+")] = 2
    d[(1, "-")] = 2
    alphabet = DIGITS | {"+", "-"}
    return DFA(alphabet, {0, 1, 2}, 0, d, {1})


class SearchTests(unittest.TestCase):
    def test_match_in_middle(self):
        self.assertTrue(digits_dfa().search("abc123def"))

    def test_no_match(self):
        self.assertFalse(digits_dfa().search("abcdef"))

    def test_match_at_end(self):
        self.assertTrue(digits_dfa().search("abc123"))

    def test_match_at_start(self):
        self.assertTrue(digits_dfa().search("123abc"))

    def test_whole_string_still_works(self):
        self.assertTrue(digits_dfa().search("123"))

    def test_empty_text_no_match(self):
        self.assertFalse(digits_dfa().search(""))

    def test_readme_example_search(self):
        dfa = arithmetic_dfa()
        self.assertTrue(dfa.search("total: 12+3-45 done"))
        # "12" on its own is already a match — the (+|-)[0-9]+ group may
        # repeat zero times — so "12+" still contains a match.
        self.assertTrue(dfa.search("total: 12+ done"))
        self.assertTrue(dfa.search("x12+3y"))
        self.assertFalse(dfa.search("no numbers here"))
        self.assertFalse(dfa.search("a+b-c"))

    def test_accept_unchanged(self):
        # Regression: the existing behaviour must not move.
        dfa = arithmetic_dfa()
        self.assertTrue(dfa.accept("12+3-45"))
        self.assertFalse(dfa.accept("12+"))
        self.assertFalse(dfa.accept("abc123"))

    def test_empty_pattern_matches_everywhere(self):
        # DFA for a* : start state is final, so the empty string matches.
        dfa = DFA({"a"}, {0}, 0, {(0, "a"): 0}, {0})
        self.assertTrue(dfa.search(""))
        self.assertTrue(dfa.search("bbb"))
        self.assertTrue(dfa.accept(""))

    def test_minimized_none_transition_does_not_crash(self):
        # minimize() writes None as the destination for undefined transitions;
        # search() must treat that as "no transition", not crash.
        d = {(0, "a"): 1, (0, "b"): None, (1, "a"): 1, (1, "b"): None}
        dfa = DFA({"a", "b"}, {0, 1}, 0, d, {1})
        self.assertTrue(dfa.search("xxaxx".replace("x", "b")))
        self.assertFalse(dfa.search("bbb"))
        self.assertTrue(dfa.search("ba"))


if __name__ == "__main__":
    unittest.main()
