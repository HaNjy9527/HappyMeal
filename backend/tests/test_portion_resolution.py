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


# --- ai_weight_hint 測試 ---

def test_resolve_portion_uses_ai_weight_hint_for_pcs_unit():
    """3 pcs 蝦，ai_weight_g=15 → resolved_weight_g=45g，method=ai_weight_hint。"""
    preset = NUTRITION_PRESETS["generic_protein"]  # plate / 180g

    portion = resolve_portion(
        food_name="蝦子",
        normalized_food_name="shrimp",
        portion_unit="pcs",
        portion_value=Decimal("3.00"),
        preset=preset,
        ai_weight_g=Decimal("15.00"),
    )

    assert portion.weight_estimation_method == "ai_weight_hint"
    assert portion.resolved_weight_g == Decimal("45.00")
    # multiplier = 45 / 180 = 0.25
    assert portion.multiplier == Decimal("0.25")


def test_resolve_portion_rejects_ai_weight_when_total_exceeds_500g():
    """4 pcs × 200g = 800g > 500g 上限 → 拒絕，走 assumed_common_serving_weight。"""
    preset = NUTRITION_PRESETS["generic_protein"]  # plate / 180g

    portion = resolve_portion(
        food_name="大蝦",
        normalized_food_name="large_shrimp",
        portion_unit="pcs",
        portion_value=Decimal("4.00"),
        preset=preset,
        ai_weight_g=Decimal("200.00"),
    )

    assert portion.weight_estimation_method == "assumed_common_serving_weight"
    # fallback: 180 × 4 = 720
    assert portion.resolved_weight_g == Decimal("720.00")


def test_resolve_portion_skips_ai_weight_for_non_countable_units():
    """bowl 不是可數單位，ai_weight_g 不應啟用步驟 4b。"""
    preset = NUTRITION_PRESETS["generic_protein"]  # plate / 180g

    portion = resolve_portion(
        food_name="蝦仁",
        normalized_food_name="shrimp_meat",
        portion_unit="bowl",
        portion_value=Decimal("1.00"),
        preset=preset,
        ai_weight_g=Decimal("50.00"),
    )

    # bowl 與 plate 同屬 container family → common_unit_conversion
    assert portion.weight_estimation_method == "common_unit_conversion"
    assert portion.weight_estimation_method != "ai_weight_hint"


def test_resolve_portion_skips_ai_weight_when_none():
    """ai_weight_g=None 時行為與既有完全相同（assumed_common_serving_weight）。"""
    preset = NUTRITION_PRESETS["generic_protein"]  # plate / 180g

    portion = resolve_portion(
        food_name="蝦子",
        normalized_food_name="shrimp",
        portion_unit="pcs",
        portion_value=Decimal("3.00"),
        preset=preset,
        ai_weight_g=None,
    )

    assert portion.weight_estimation_method == "assumed_common_serving_weight"
    assert portion.resolved_weight_g == Decimal("540.00")  # 180 × 3
