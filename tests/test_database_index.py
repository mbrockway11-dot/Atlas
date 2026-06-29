from atlas.database.index import (
    find_entity,
    list_entities,
    load_database_index,
    upsert_entity,
)


def test_load_database_index():
    index = load_database_index()

    assert "version" in index
    assert "entities" in index


def test_upsert_entity():
    entity = upsert_entity(
        name="Nikola Tesla",
        entity_type="person",
        tags=["science", "inventor"],
        birth_confidence="medium",
        notes="Historical seed profile.",
    )

    assert entity["id"] == "nikola_tesla"
    assert entity["name"] == "Nikola Tesla"
    assert entity["entity_type"] == "person"
    assert "science" in entity["tags"]

    found = find_entity("nikola_tesla")

    assert found is not None
    assert found["name"] == "Nikola Tesla"


def test_list_entities():
    entities = list_entities()

    assert isinstance(entities, list)