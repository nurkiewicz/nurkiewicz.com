from pathlib import Path

import pytest

GLOSSARY = Path(__file__).resolve().parents[2] / "docs" / "polski-w-it.md"

PR = "https://github.com/nurkiewicz/polski-w-it/pull/"

# Words with no good Polish equivalent, deliberately left untranslated.
# Each maps to discussion of proposed translations that were rejected.
UNTRANSLATABLE = {
    "bean": [PR + "12"],
    "branch": [PR + "118"],
    "commit": [PR + "117", PR + "145/files"],
    "framework": [PR + "15"],
    "garbage collector": [PR + "19"],
    "legacy": [PR + "144"],
    "lint": [PR + "248"],
    "merge": [PR + "178"],
    "pipeline": [PR + "90"],
    "pull": [],
    "pull request": [],
    "push": [],
}


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
    for term in english_terms:
        assert term not in UNTRANSLATABLE, (
            f"'{term}' is untranslatable, see rejected proposals: "
            f"{UNTRANSLATABLE[term] or 'none yet'}"
        )
