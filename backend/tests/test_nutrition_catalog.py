from app.services.nutrition_catalog import lookup_official_nutrition


def test_lookup_official_nutrition_matches_black_coffee():
    record = lookup_official_nutrition(
        food_name="Black Coffee",
        normalized_food_name="black_coffee",
    )

    assert record is not None
    assert record.canonical_food_name == "black_coffee"
    assert record.source == "official_source"


def test_lookup_official_nutrition_matches_alias():
    record = lookup_official_nutrition(
        food_name="Americano",
        normalized_food_name="americano",
    )

    assert record is not None
    assert record.canonical_food_name == "black_coffee"


def test_lookup_official_nutrition_matches_white_rice():
    record = lookup_official_nutrition(
        food_name="White Rice",
        normalized_food_name="white_rice",
    )

    assert record is not None
    assert record.canonical_food_name == "white_rice"


def test_lookup_official_nutrition_returns_none_for_unknown_food():
    record = lookup_official_nutrition(
        food_name="Mystery Food",
        normalized_food_name="mystery_food",
    )

    assert record is None
