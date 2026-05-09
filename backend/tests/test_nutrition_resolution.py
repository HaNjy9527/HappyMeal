from decimal import Decimal

from app.services.nutrition_resolution import NutritionResolutionInput, resolve_item_nutrition


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


def test_resolve_item_nutrition_returns_alias_mapping_for_known_alias():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="White Rice",
            normalized_food_name="white_rice",
            portion_value=Decimal("1.00"),
            portion_unit="bowl",
        )
    )

    assert result.canonical_food_name == "generic_rice"
    assert result.nutrition_source == "alias_mapping"
    assert result.is_estimated is True
    assert result.kcal == Decimal("216.00")


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


def test_resolve_item_nutrition_uses_drink_fallback_for_black_coffee_bottle():
    result = resolve_item_nutrition(
        NutritionResolutionInput(
            food_name="Black Coffee",
            normalized_food_name="black_coffee",
            portion_value=Decimal("1.00"),
            portion_unit="bottle",
        )
    )

    assert result.canonical_food_name == "generic_unsweetened_drink"
    assert result.nutrition_source == "drink_fallback"
    assert result.is_estimated is True
    assert result.resolved_weight_g == Decimal("375.00")
    assert result.weight_estimation_method == "drink_container_default"
    assert result.kcal == Decimal("7.50")


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
