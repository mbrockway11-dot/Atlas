from atlas.explanation import (
    explain_archetype,
    explain_planet,
    explain_relationship,
    explain_role,
)


def test_explain_planet():
    assert "persistence" in explain_planet("Saturn")


def test_explain_role():
    assert "connectivity" in explain_role("hub")


def test_explain_archetype():
    assert "Primary measurements" in explain_archetype("hub_dominant")


def test_explain_relationship():
    text = explain_relationship(
        planet_a="Saturn",
        planet_b="Jupiter",
        similarity=0.8,
        distance=0.2,
        agreement=0.7,
    )

    assert "Saturn" in text
    assert "Jupiter" in text
    assert "strong structural alignment" in text