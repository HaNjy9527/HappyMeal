from decimal import Decimal

from app.services.portion_resolution import NUTRITION_PRESETS, resolve_nutrition_preset, resolve_portion


def test_resolve_portion_converts_ml_units_to_grams_for_drinks():
    preset = NUTRITION_PRESETS["generic_unsweetened_drink"]

    portion = resolve_portion(
        food_name="Black Tea",
        normalized_food_name="black_tea",
        portion_unit="ml",
        portion_value=Decimal("330.00"),
        preset=preset,
    )

    assert portion.portion_unit == "ml"
    assert portion.resolved_weight_g == Decimal("330.00")
    assert portion.weight_estimation_method == "direct_milliliters"


def test_resolve_portion_converts_liters_to_grams_for_drinks():
    preset = NUTRITION_PRESETS["generic_unsweetened_drink"]

    portion = resolve_portion(
        food_name="Black Tea",
        normalized_food_name="black_tea",
        portion_unit="liter",
        portion_value=Decimal("1.50"),
        preset=preset,
    )

    assert portion.portion_unit == "l"
    assert portion.resolved_weight_g == Decimal("1500.00")
    assert portion.weight_estimation_method == "direct_milliliters"


def test_resolve_portion_uses_container_defaults_for_drinks():
    preset = NUTRITION_PRESETS["generic_unsweetened_drink"]

    portion = resolve_portion(
        food_name="Bottled Coffee",
        normalized_food_name="tea_drink",
        portion_unit="bottle",
        portion_value=Decimal("1.00"),
        preset=preset,
    )

    assert portion.portion_unit == "bottle"
    assert portion.resolved_weight_g == Decimal("375.00")
    assert portion.weight_estimation_method == "drink_container_default"


def test_resolve_portion_uses_serving_default_for_drinks():
    preset = NUTRITION_PRESETS["generic_unsweetened_drink"]

    portion = resolve_portion(
        food_name="Tea Drink",
        normalized_food_name="tea_drink",
        portion_unit="serving",
        portion_value=Decimal("1.00"),
        preset=preset,
    )

    assert portion.portion_unit == "serving"
    assert portion.resolved_weight_g == Decimal("240.00")
    assert portion.weight_estimation_method == "drink_serving_default"


def test_resolve_portion_keeps_common_unit_conversion_for_non_drinks():
    preset = NUTRITION_PRESETS["grilled_chicken_rice"]

    portion = resolve_portion(
        food_name="Chicken Rice",
        normalized_food_name="grilled_chicken_rice",
        portion_unit="bowl",
        portion_value=Decimal("1.00"),
        preset=preset,
    )

    assert portion.portion_unit == "bowl"
    assert portion.resolved_weight_g == Decimal("324.00")
    assert portion.weight_estimation_method == "common_unit_conversion"


def test_resolve_nutrition_preset_uses_drink_fallback_for_packaged_drinks():
    resolved = resolve_nutrition_preset(
        food_name="Black Coffee",
        normalized_food_name="black_coffee",
        canonical_food_name="generic_mixed_meal",
        nutrition_source="default_fallback",
        is_estimated=True,
    )

    assert resolved.canonical_food_name == "generic_unsweetened_drink"
    assert resolved.nutrition_source == "drink_fallback"
    assert resolved.is_estimated is True
