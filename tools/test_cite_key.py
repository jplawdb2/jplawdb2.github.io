#!/usr/bin/env python3
"""Unit tests for cite_key <-> article_id conversion.

Usage:
    python3 tools/test_cite_key.py
"""

import re
import sys
import unittest

# cite_key -> (code, article_id) mapping
# cite_key format: {prefix}{article_display}
# article_display: digits with "の" separators (laws) or "-" separators (tsutatsu)
# article_id: "の" replaced with "_", "-" kept as-is

# Known cite prefixes and their codes
PREFIX_TO_CODE = {
    "法法": "hojin",
    "法令": "hojin-rei",
    "法規": "hojin-ki",
    "措法": "sochi",
    "措令": "sochi-rei",
    "措規": "sochi-ki",
    "所法": "shotoku",
    "所令": "shotoku-rei",
    "消法": "shohi",
    "相法": "sozoku",
    "法基通": "hojin-kihon",
    "所基通": "shotoku-kihon",
    "消基通": "shohi-kihon",
    "措通法": "sochi-tsu-hojin",
    "措通所": "sochi-tsu-shotoku",
    "相基通": "sozoku-kihon",
}

# Sorted by prefix length descending to match longest first
SORTED_PREFIXES = sorted(PREFIX_TO_CODE.keys(), key=len, reverse=True)


def cite_key_to_code_and_id(cite_key: str) -> tuple:
    """Convert a cite_key to (code, article_id).

    Examples:
        "法法22"       -> ("hojin", "22")
        "法法22の2"    -> ("hojin", "22_2")
        "措法66の6"    -> ("sochi", "66_6")
        "法基通2-1-1"  -> ("hojin-kihon", "2-1-1")
        "措通法66の6-1" -> ("sochi-tsu-hojin", "66_6-1")
    """
    # Match longest prefix first
    matched_prefix = None
    for prefix in SORTED_PREFIXES:
        if cite_key.startswith(prefix):
            matched_prefix = prefix
            break

    if matched_prefix is None:
        raise ValueError(f"Unknown cite_key prefix: {cite_key}")

    code = PREFIX_TO_CODE[matched_prefix]
    article_display = cite_key[len(matched_prefix):]

    # Convert display form to article_id: "の" -> "_"
    article_id = article_display.replace("の", "_")

    return (code, article_id)


def article_id_to_display(article_id: str) -> str:
    """Convert article_id to display form.

    "66_6" -> "66の6"
    "2-1-1" -> "2-1-1"
    "10_4_2_3" -> "10の4の2の3"
    """
    return article_id.replace("_", "の")


def code_and_id_to_url(code: str, article_id: str) -> str:
    """Build the full URL for a given code and article_id."""
    return f"https://jplawdb2.github.io/text/{code}/{article_id}.txt"


class TestCiteKeyConversion(unittest.TestCase):
    """Test cite_key -> (code, article_id) conversion."""

    def test_known_cases(self):
        cases = [
            ("法法22", "hojin", "22"),
            ("法法22の2", "hojin", "22_2"),
            ("措法66の6", "sochi", "66_6"),
            ("法法10の4の2の3", "hojin", "10_4_2_3"),
            ("法基通2-1-1", "hojin-kihon", "2-1-1"),
            ("措通法66の6-1", "sochi-tsu-hojin", "66_6-1"),
        ]
        for cite_key, expected_code, expected_id in cases:
            with self.subTest(cite_key=cite_key):
                code, article_id = cite_key_to_code_and_id(cite_key)
                self.assertEqual(code, expected_code,
                                 f"cite_key={cite_key}: code={code}, expected={expected_code}")
                self.assertEqual(article_id, expected_id,
                                 f"cite_key={cite_key}: id={article_id}, expected={expected_id}")

    def test_additional_law_codes(self):
        """Test other law types."""
        cases = [
            ("所法28", "shotoku", "28"),
            ("消法30", "shohi", "30"),
            ("相法22", "sozoku", "22"),
            ("法令69の2", "hojin-rei", "69_2"),
            ("措令39の14", "sochi-rei", "39_14"),
            ("所基通36-15", "shotoku-kihon", "36-15"),
            ("消基通5-1-1", "shohi-kihon", "5-1-1"),
        ]
        for cite_key, expected_code, expected_id in cases:
            with self.subTest(cite_key=cite_key):
                code, article_id = cite_key_to_code_and_id(cite_key)
                self.assertEqual(code, expected_code)
                self.assertEqual(article_id, expected_id)

    def test_url_generation(self):
        """Test full URL generation."""
        cases = [
            ("法法22", "https://jplawdb2.github.io/text/hojin/22.txt"),
            ("措法66の6", "https://jplawdb2.github.io/text/sochi/66_6.txt"),
            ("法基通2-1-1", "https://jplawdb2.github.io/text/hojin-kihon/2-1-1.txt"),
        ]
        for cite_key, expected_url in cases:
            with self.subTest(cite_key=cite_key):
                code, article_id = cite_key_to_code_and_id(cite_key)
                url = code_and_id_to_url(code, article_id)
                self.assertEqual(url, expected_url)

    def test_display_roundtrip(self):
        """Test article_id -> display -> back conversion."""
        cases = [
            ("22", "22"),
            ("22_2", "22の2"),
            ("66_6", "66の6"),
            ("10_4_2_3", "10の4の2の3"),
            ("2-1-1", "2-1-1"),
        ]
        for article_id, expected_display in cases:
            with self.subTest(article_id=article_id):
                display = article_id_to_display(article_id)
                self.assertEqual(display, expected_display)
                # Roundtrip: display -> id
                back = display.replace("の", "_")
                self.assertEqual(back, article_id)

    def test_unknown_prefix_raises(self):
        """Unknown prefix should raise ValueError."""
        with self.assertRaises(ValueError):
            cite_key_to_code_and_id("不明99")

    def test_mixed_underscore_and_dash(self):
        """Tsutatsu cite_keys with both の and - in display form."""
        # 措通法66の6-1 -> code=sochi-tsu-hojin, id=66_6-1
        code, article_id = cite_key_to_code_and_id("措通法66の6-1")
        self.assertEqual(code, "sochi-tsu-hojin")
        self.assertEqual(article_id, "66_6-1")
        # The "-" is preserved, only "の" -> "_"
        self.assertIn("-", article_id)
        self.assertNotIn("の", article_id)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
