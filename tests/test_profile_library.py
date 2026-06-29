from atlas.library.profile_library import safe_name


def test_safe_name():
    assert safe_name("Michael Elvis Brockway") == "michael_elvis_brockway"
    assert safe_name("Jean-Luc O'Neill") == "jean_luc_oneill"