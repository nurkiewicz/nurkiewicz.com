from pathlib import Path

import pytest

GLOSSARY = Path(__file__).resolve().parents[2] / "docs" / "polski-w-it" / "index.md"

# Words that have no good Polish equivalent and are deliberately left untranslated
UNTRANSLATABLE = [
    "bean",
    "branch",
    "commit",
    "framework",
    "garbage collector",
    "legacy",
    "lint",
    "merge",
    "pipeline",
    "pull",
    "pull request",
    "push",
]


@pytest.fixture
def english_terms():
    with open(GLOSSARY, "r", encoding="utf-8") as glossary:
        lines = [line.strip() for line in glossary.readlines()]
    table = [line for line in lines if line.startswith("|")]
    header, separator, *rows = table
    assert header.startswith("| angielski |")
    assert set(separator) <= set("|-: ")
    return [row.strip("|").split("|")[0].strip() for row in rows]


def test_has_terms(english_terms):
    assert len(english_terms) > 100


def test_terms_are_sorted(english_terms):
    assert english_terms == sorted(english_terms, key=str.lower)


def test_does_not_contain_untranslateble_words(english_terms):
    assert not set(english_terms) & set(UNTRANSLATABLE)
