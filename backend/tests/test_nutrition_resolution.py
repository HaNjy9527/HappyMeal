from decimal import Decimal

from app.services.nutrition_resolution import (
    NutritionResolutionInput,
    resolve_official_source,
    resolve_item_nutrition,
    select_nutrition_source,
)


def test_resolve_official_source_matches_curated_catalog():
    candidate = resolve_official_source(
        NutritionResolutionInput(
            food_name="Black Coffee",
            normalized_food_name="black_coffee",
            portion_value=Decimal("1.00"),
            portion_unit="bottle",
        )
    )

    assert candidate.source == "official_source"
    assert candidate.canonical_food_name == "black_coffee"
    assert candidate.is_estimated is False
    assert candidate.matched is True
    assert candidate.preset is not None


def test_resolve_official_source_returns_unmatched_for_unknown_food():
    candidate = resolve_official_source(
        NutritionResolutionInput(
            food_name="Mystery Food",
            normalized_food_name="mystery_food",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert candidate.source == "official_source"
    assert candidate.matched is False


def test_resolve_item_nutrition_returns_direct_preset_for_known_food():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Chicken Salad",
            normalized_food_name="chicken_salad",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
            confidence_score=Decimal("0.942"),
        )
    )

    assert result.canonical_food_name == "chicken_salad"
    assert result.nutrition_source == "preset"
    assert result.is_estimated is False
    assert result.resolved_weight_g == Decimal("280.00")
    assert result.weight_estimation_method == "exact_unit_match"
    assert result.kcal == Decimal("320.00")
    assert result.confidence_score == Decimal("0.942")

    decision = select_nutrition_source(
        NutritionResolutionInput(
            food_name="Chicken Salad",
            normalized_food_name="chicken_salad",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert decision.source == "preset"
    assert decision.priority == "canonical_mapping"


def test_resolve_item_nutrition_returns_official_source_for_white_rice():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="White Rice",
            normalized_food_name="white_rice",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert result.canonical_food_name == "white_rice"
    assert result.nutrition_source == "official_source"
    assert result.is_estimated is False
    assert result.kcal == Decimal("216.00")


def test_resolve_item_nutrition_returns_official_source_for_boiled_egg():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Boiled Egg",
            normalized_food_name="boiled_egg",
            portion_value=Decimal("1.00"),
            portion_unit="pcs",
        )
    )

    assert result.canonical_food_name == "boiled_egg"
    assert result.nutrition_source == "official_source"
    assert result.is_estimated is False
    assert result.kcal == Decimal("78.00")


def test_resolve_item_nutrition_returns_keyword_fallback_for_keyword_match():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Chili Sauce",
            normalized_food_name="mystery_condiment",
            portion_value=Decimal("1.00"),
            portion_unit="tbsp",
        )
    )

    assert result.canonical_food_name == "generic_condiment"
    assert result.nutrition_source == "keyword_fallback"
    assert result.is_estimated is True
    assert result.kcal == Decimal("35.00")


def test_resolve_item_nutrition_returns_default_fallback_for_unknown_food():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Mystery Food",
            normalized_food_name="mystery_food",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert result.canonical_food_name == "generic_mixed_meal"
    assert result.nutrition_source == "default_fallback"
    assert result.is_estimated is True
    assert result.kcal > Decimal("0.00")

    decision = select_nutrition_source(
        NutritionResolutionInput(
            food_name="Mystery Food",
            normalized_food_name="mystery_food",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert decision.source == "default_fallback"
    assert decision.priority == "fallback_estimate"


def test_resolve_item_nutrition_uses_official_source_for_black_coffee_bottle():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Black Coffee",
            normalized_food_name="black_coffee",
            portion_value=Decimal("1.00"),
            portion_unit="bottle",
        )
    )

    assert result.canonical_food_name == "black_coffee"
    assert result.nutrition_source == "official_source"
    assert result.is_estimated is False
    assert result.resolved_weight_g == Decimal("375.00")
    assert result.weight_estimation_method == "drink_container_default"
    assert result.kcal == Decimal("7.50")

    decision = select_nutrition_source(
        NutritionResolutionInput(
            food_name="Black Coffee",
            normalized_food_name="black_coffee",
            portion_value=Decimal("1.00"),
            portion_unit="bottle",
        )
    )

    assert decision.source == "official_source"
    assert decision.priority == "official_source"


def test_resolve_item_nutrition_uses_direct_milliliters_for_tea_drink():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Tea Drink",
            normalized_food_name="tea_drink",
            portion_value=Decimal("330.00"),
            portion_unit="ml",
        )
    )

    assert result.canonical_food_name == "generic_unsweetened_drink"
    assert result.nutrition_source == "drink_fallback"
    assert result.portion_unit == "ml"
    assert result.resolved_weight_g == Decimal("330.00")
    assert result.weight_estimation_method == "direct_milliliters"
    assert result.kcal == Decimal("6.60")
