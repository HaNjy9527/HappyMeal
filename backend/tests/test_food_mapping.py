from app.services.food_mapping import resolve_canonical_food


def test_resolve_canonical_food_returns_direct_match_for_known_canonical_key():
    result = resolve_canonical_food(food_name="Chicken Salad", normalized_food_name="chicken_salad")

    assert result.canonical_food_name == "chicken_salad"
    assert result.match_type == "direct"
    assert result.matched_term == "chicken_salad"
    assert result.is_estimated is False


def test_resolve_canonical_food_returns_alias_match():
    result = resolve_canonical_food(food_name="白飯", normalized_food_name="white_rice")

    assert result.canonical_food_name == "generic_rice"
    assert result.match_type == "alias"
    assert result.matched_term == "white_rice"
    assert result.is_estimated is True


def test_resolve_canonical_food_returns_alias_match_for_mixed_meal():
    result = resolve_canonical_food(food_name="雞肉飯", normalized_food_name="chicken_rice_bowl")

    assert result.canonical_food_name == "generic_mixed_meal"
    assert result.match_type == "alias"
    assert result.matched_term == "chicken_rice_bowl"
    assert result.is_estimated is True


def test_resolve_canonical_food_returns_keyword_match_for_condiment():
    result = resolve_canonical_food(food_name="辣椒醬", normalized_food_name="mystery_condiment")

    assert result.canonical_food_name == "generic_condiment"
    assert result.match_type == "keyword"
    assert result.matched_term == "醬"
    assert result.is_estimated is True


def test_resolve_canonical_food_returns_keyword_match_for_garnish():
    result = resolve_canonical_food(food_name="薑絲", normalized_food_name="mystery_garnish")

    assert result.canonical_food_name == "generic_garnish"
    assert result.match_type == "keyword"
    assert result.matched_term == "薑"
    assert result.is_estimated is True


def test_resolve_canonical_food_returns_keyword_match_for_mixed_meal_rice_and_protein():
    result = resolve_canonical_food(food_name="雞肉飯", normalized_food_name="mystery_lunch")

    assert result.canonical_food_name == "generic_mixed_meal"
    assert result.match_type == "keyword"
    assert result.matched_term == "飯+雞"
    assert result.is_estimated is True


def test_resolve_canonical_food_returns_default_fallback_for_unknown_food():
    result = resolve_canonical_food(food_name="神秘料理", normalized_food_name="mystery_food")

    assert result.canonical_food_name == "generic_mixed_meal"
    assert result.match_type == "default_fallback"
    assert result.matched_term == "generic_mixed_meal"
    assert result.is_estimated is True
