from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class NutritionPreset:
    portion_unit: str
    portion_weight_g: Decimal
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carb_g: Decimal


@dataclass(frozen=True)
class ResolvedNutritionPreset:
    canonical_food_name: str
    nutrition_source: str
    is_estimated: bool
    preset: NutritionPreset


@dataclass(frozen=True)
class PortionResolution:
    source_portion_unit: str
    portion_unit: str
    resolved_weight_g: Decimal
    weight_estimation_method: str
    multiplier: Decimal


NUTRITION_PRESETS = {
    "chicken_salad": NutritionPreset("bowl", Decimal("280.00"), Decimal("320.00"), Decimal("28.00"), Decimal("18.00"), Decimal("12.00")),
    "boiled_egg": NutritionPreset("pcs", Decimal("50.00"), Decimal("78.00"), Decimal("6.50"), Decimal("5.30"), Decimal("0.60")),
    "grilled_chicken_rice": NutritionPreset("plate", Decimal("360.00"), Decimal("520.00"), Decimal("34.00"), Decimal("12.00"), Decimal("63.00")),
    "stir_fried_vegetables": NutritionPreset("plate", Decimal("250.00"), Decimal("160.00"), Decimal("5.00"), Decimal("7.00"), Decimal("18.00")),
    "grilled_salmon": NutritionPreset("fillet", Decimal("150.00"), Decimal("280.00"), Decimal("26.00"), Decimal("18.00"), Decimal("0.00")),
    "brown_rice": NutritionPreset("bowl", Decimal("160.00"), Decimal("216.00"), Decimal("5.00"), Decimal("1.80"), Decimal("45.00")),
    "steamed_broccoli": NutritionPreset("bowl", Decimal("90.00"), Decimal("55.00"), Decimal("3.70"), Decimal("0.60"), Decimal("11.00")),
    "generic_mixed_meal": NutritionPreset("bowl", Decimal("320.00"), Decimal("420.00"), Decimal("20.00"), Decimal("14.00"), Decimal("52.00")),
    "generic_rice": NutritionPreset("bowl", Decimal("160.00"), Decimal("216.00"), Decimal("5.00"), Decimal("1.80"), Decimal("45.00")),
    "generic_vegetables": NutritionPreset("bowl", Decimal("100.00"), Decimal("60.00"), Decimal("3.00"), Decimal("0.80"), Decimal("10.00")),
    "generic_condiment": NutritionPreset("tbsp", Decimal("15.00"), Decimal("35.00"), Decimal("0.50"), Decimal("2.00"), Decimal("3.00")),
    "generic_garnish": NutritionPreset("tbsp", Decimal("6.00"), Decimal("8.00"), Decimal("0.20"), Decimal("0.10"), Decimal("1.50")),
    "generic_protein": NutritionPreset("plate", Decimal("180.00"), Decimal("260.00"), Decimal("26.00"), Decimal("14.00"), Decimal("4.00")),
    "generic_unsweetened_drink": NutritionPreset("g", Decimal("100.00"), Decimal("2.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.50")),
    # --- 便當 ---
    "chicken_leg_bento": NutritionPreset("box", Decimal("650.00"), Decimal("750.00"), Decimal("32.00"), Decimal("22.00"), Decimal("95.00")),
    "pork_chop_bento": NutritionPreset("box", Decimal("650.00"), Decimal("800.00"), Decimal("30.00"), Decimal("28.00"), Decimal("95.00")),
    "braised_pork_bento": NutritionPreset("box", Decimal("600.00"), Decimal("750.00"), Decimal("26.00"), Decimal("25.00"), Decimal("90.00")),
    "fish_fillet_bento": NutritionPreset("box", Decimal("600.00"), Decimal("680.00"), Decimal("28.00"), Decimal("18.00"), Decimal("90.00")),
    "vegetarian_bento": NutritionPreset("box", Decimal("550.00"), Decimal("580.00"), Decimal("16.00"), Decimal("14.00"), Decimal("90.00")),
    # --- 飯類 ---
    "minced_pork_rice": NutritionPreset("bowl", Decimal("250.00"), Decimal("380.00"), Decimal("12.00"), Decimal("11.00"), Decimal("55.00")),
    "shredded_chicken_rice": NutritionPreset("bowl", Decimal("250.00"), Decimal("320.00"), Decimal("14.00"), Decimal("6.00"), Decimal("52.00")),
    "pork_chop_rice": NutritionPreset("plate", Decimal("380.00"), Decimal("580.00"), Decimal("24.00"), Decimal("18.00"), Decimal("78.00")),
    "fried_rice": NutritionPreset("plate", Decimal("280.00"), Decimal("450.00"), Decimal("12.00"), Decimal("14.00"), Decimal("68.00")),
    "curry_rice": NutritionPreset("plate", Decimal("380.00"), Decimal("550.00"), Decimal("18.00"), Decimal("14.00"), Decimal("85.00")),
    # --- 麵食 ---
    "beef_noodle_soup": NutritionPreset("bowl", Decimal("650.00"), Decimal("620.00"), Decimal("30.00"), Decimal("18.00"), Decimal("85.00")),
    "plain_noodle_soup": NutritionPreset("bowl", Decimal("400.00"), Decimal("330.00"), Decimal("12.00"), Decimal("4.00"), Decimal("62.00")),
    "dan_zai_noodle": NutritionPreset("bowl", Decimal("350.00"), Decimal("290.00"), Decimal("14.00"), Decimal("6.00"), Decimal("48.00")),
    "dry_noodle": NutritionPreset("bowl", Decimal("250.00"), Decimal("400.00"), Decimal("12.00"), Decimal("14.00"), Decimal("57.00")),
    "rice_noodle_soup": NutritionPreset("bowl", Decimal("400.00"), Decimal("280.00"), Decimal("8.00"), Decimal("5.00"), Decimal("52.00")),
    "steamed_dumpling": NutritionPreset("serving", Decimal("250.00"), Decimal("420.00"), Decimal("18.00"), Decimal("12.00"), Decimal("58.00")),
    "pan_fried_dumpling": NutritionPreset("serving", Decimal("180.00"), Decimal("380.00"), Decimal("14.00"), Decimal("16.00"), Decimal("48.00")),
    # --- 蛋白質 ---
    "chicken_leg": NutritionPreset("pcs", Decimal("200.00"), Decimal("280.00"), Decimal("26.00"), Decimal("18.00"), Decimal("0.00")),
    "fried_chicken_cutlet": NutritionPreset("pcs", Decimal("200.00"), Decimal("460.00"), Decimal("28.00"), Decimal("24.00"), Decimal("30.00")),
    "pork_chop": NutritionPreset("pcs", Decimal("180.00"), Decimal("360.00"), Decimal("26.00"), Decimal("22.00"), Decimal("12.00")),
    "braised_pork_belly": NutritionPreset("serving", Decimal("150.00"), Decimal("380.00"), Decimal("18.00"), Decimal("28.00"), Decimal("8.00")),
    # --- 湯 ---
    "fish_ball_soup": NutritionPreset("bowl", Decimal("350.00"), Decimal("180.00"), Decimal("12.00"), Decimal("6.00"), Decimal("18.00")),
    "egg_drop_soup": NutritionPreset("bowl", Decimal("300.00"), Decimal("80.00"), Decimal("6.00"), Decimal("4.00"), Decimal("4.00")),
    "radish_pork_rib_soup": NutritionPreset("bowl", Decimal("380.00"), Decimal("260.00"), Decimal("18.00"), Decimal("14.00"), Decimal("14.00")),
    "miso_soup": NutritionPreset("bowl", Decimal("250.00"), Decimal("55.00"), Decimal("3.00"), Decimal("2.00"), Decimal("5.00")),
    # --- 配菜 ---
    "braised_egg": NutritionPreset("pcs", Decimal("60.00"), Decimal("95.00"), Decimal("7.00"), Decimal("6.00"), Decimal("2.00")),
    "tofu": NutritionPreset("g", Decimal("100.00"), Decimal("76.00"), Decimal("8.00"), Decimal("4.00"), Decimal("2.00")),
    "braised_tofu": NutritionPreset("serving", Decimal("150.00"), Decimal("140.00"), Decimal("12.00"), Decimal("7.00"), Decimal("8.00")),
    "pig_blood_cake": NutritionPreset("serving", Decimal("100.00"), Decimal("200.00"), Decimal("8.00"), Decimal("2.00"), Decimal("38.00")),
    "stir_fried_morning_glory": NutritionPreset("g", Decimal("100.00"), Decimal("65.00"), Decimal("2.00"), Decimal("4.00"), Decimal("5.00")),
    "stir_fried_cabbage": NutritionPreset("g", Decimal("100.00"), Decimal("55.00"), Decimal("2.00"), Decimal("3.00"), Decimal("5.00")),
    # --- 飲料 ---
    "unsweetened_soy_milk": NutritionPreset("cup", Decimal("250.00"), Decimal("70.00"), Decimal("5.00"), Decimal("3.00"), Decimal("5.00")),
    "sweetened_soy_milk": NutritionPreset("cup", Decimal("250.00"), Decimal("120.00"), Decimal("5.00"), Decimal("3.00"), Decimal("18.00")),
    "rice_milk": NutritionPreset("cup", Decimal("250.00"), Decimal("180.00"), Decimal("2.00"), Decimal("4.00"), Decimal("33.00")),
    "bubble_milk_tea": NutritionPreset("cup", Decimal("500.00"), Decimal("400.00"), Decimal("3.00"), Decimal("5.00"), Decimal("85.00")),
    # --- 輕食 / 早餐 ---
    "oatmeal": NutritionPreset("bowl", Decimal("250.00"), Decimal("150.00"), Decimal("5.00"), Decimal("3.00"), Decimal("27.00")),
    "greek_yogurt": NutritionPreset("cup", Decimal("200.00"), Decimal("130.00"), Decimal("17.00"), Decimal("0.70"), Decimal("10.00")),
    "avocado_toast": NutritionPreset("pcs", Decimal("130.00"), Decimal("240.00"), Decimal("6.00"), Decimal("14.00"), Decimal("24.00")),
    "sandwich": NutritionPreset("pcs", Decimal("180.00"), Decimal("280.00"), Decimal("12.00"), Decimal("8.00"), Decimal("38.00")),
    "rice_ball": NutritionPreset("pcs", Decimal("150.00"), Decimal("230.00"), Decimal("7.00"), Decimal("4.00"), Decimal("43.00")),
    "tuna_salad": NutritionPreset("bowl", Decimal("250.00"), Decimal("220.00"), Decimal("20.00"), Decimal("10.00"), Decimal("12.00")),
    # --- 水果 ---
    "banana": NutritionPreset("pcs", Decimal("120.00"), Decimal("105.00"), Decimal("1.30"), Decimal("0.40"), Decimal("27.00")),
    "apple": NutritionPreset("pcs", Decimal("180.00"), Decimal("95.00"), Decimal("0.50"), Decimal("0.30"), Decimal("25.00")),
    "mixed_fruits": NutritionPreset("bowl", Decimal("200.00"), Decimal("100.00"), Decimal("1.00"), Decimal("0.50"), Decimal("25.00")),
    # --- 咖啡 / 飲品 ---
    "latte": NutritionPreset("cup", Decimal("240.00"), Decimal("120.00"), Decimal("6.00"), Decimal("4.00"), Decimal("14.00")),
    "matcha_latte": NutritionPreset("cup", Decimal("240.00"), Decimal("160.00"), Decimal("6.00"), Decimal("5.00"), Decimal("22.00")),
    "fruit_smoothie": NutritionPreset("cup", Decimal("300.00"), Decimal("180.00"), Decimal("3.00"), Decimal("1.50"), Decimal("42.00")),
    # --- 台灣常見輕食 ---
    "spring_roll": NutritionPreset("pcs", Decimal("200.00"), Decimal("280.00"), Decimal("8.00"), Decimal("8.00"), Decimal("44.00")),
    "congee": NutritionPreset("bowl", Decimal("300.00"), Decimal("150.00"), Decimal("3.00"), Decimal("0.50"), Decimal("34.00")),
    # --- 台式早餐 ---
    "egg_crepe": NutritionPreset("pcs", Decimal("150.00"), Decimal("280.00"), Decimal("10.00"), Decimal("10.00"), Decimal("36.00")),
    "sesame_flatbread": NutritionPreset("pcs", Decimal("160.00"), Decimal("430.00"), Decimal("11.00"), Decimal("18.00"), Decimal("58.00")),
    "steamed_bun": NutritionPreset("pcs", Decimal("100.00"), Decimal("220.00"), Decimal("7.00"), Decimal("2.00"), Decimal("44.00")),
    "toast": NutritionPreset("pcs", Decimal("60.00"), Decimal("160.00"), Decimal("5.00"), Decimal("3.00"), Decimal("28.00")),
    # --- 夜市小吃 ---
    "oyster_noodles": NutritionPreset("bowl", Decimal("350.00"), Decimal("260.00"), Decimal("10.00"), Decimal("4.00"), Decimal("48.00")),
    "oyster_omelette": NutritionPreset("pcs", Decimal("200.00"), Decimal("320.00"), Decimal("10.00"), Decimal("12.00"), Decimal("44.00")),
    "popcorn_chicken": NutritionPreset("serving", Decimal("150.00"), Decimal("420.00"), Decimal("22.00"), Decimal("24.00"), Decimal("30.00")),
    "scallion_pancake": NutritionPreset("pcs", Decimal("100.00"), Decimal("310.00"), Decimal("6.00"), Decimal("14.00"), Decimal("42.00")),
    "taiwanese_sausage_rice": NutritionPreset("pcs", Decimal("200.00"), Decimal("520.00"), Decimal("14.00"), Decimal("16.00"), Decimal("80.00")),
    # --- 甜湯甜點 ---
    "red_bean_soup": NutritionPreset("bowl", Decimal("300.00"), Decimal("180.00"), Decimal("6.00"), Decimal("0.50"), Decimal("38.00")),
    "grass_jelly": NutritionPreset("cup", Decimal("300.00"), Decimal("120.00"), Decimal("1.00"), Decimal("0.50"), Decimal("28.00")),
    "taro_balls": NutritionPreset("serving", Decimal("200.00"), Decimal("260.00"), Decimal("3.00"), Decimal("1.00"), Decimal("58.00")),
}

UNIT_ALIASES = {
    "gram": "g",
    "grams": "g",
    "plates": "plate",
    "dish": "plate",
    "dishes": "plate",
    "bowls": "bowl",
    "cups": "cup",
    "servings": "serving",
    "portion": "serving",
    "portions": "serving",
    "pieces": "pcs",
    "piece": "pcs",
    "pc": "pcs",
    "fillets": "fillet",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "spoon": "tbsp",
    "spoons": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "bags": "bag",
    "boxes": "box",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "bottles": "bottle",
    "cans": "can",
}

UNIT_FAMILIES = {
    "container": {
        "plate": Decimal("1.00"),
        "bowl": Decimal("0.90"),
        "box": Decimal("1.00"),
        "bag": Decimal("1.00"),
        "cup": Decimal("0.75"),
        "serving": Decimal("1.00"),
    },
    "piece": {
        "pcs": Decimal("1.00"),
        "fillet": Decimal("1.00"),
    },
    "spoon": {
        "tbsp": Decimal("1.00"),
        "tsp": Decimal("0.33"),
    },
}

DRINK_VOLUME_ML_BY_UNIT = {
    "can": Decimal("330.00"),
    "bottle": Decimal("375.00"),
    "cup": Decimal("240.00"),
    "serving": Decimal("240.00"),
}

DIRECT_DRINK_NAMES = {
    "black_coffee",
    "americano",
    "black_tea",
    "green_tea",
    "tea_drink",
}

DRINK_KEYWORDS = ("coffee", "tea", "drink", "beverage")

COUNTABLE_UNITS = {"pcs", "piece", "slice", "個", "片"}
AI_WEIGHT_MAX_G = Decimal("500.00")


def quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def normalize_portion_unit(unit: str) -> str:
    normalized_unit = unit.strip().lower()
    return UNIT_ALIASES.get(normalized_unit, normalized_unit)


def is_packaged_drink(*, food_name: str, normalized_food_name: str) -> bool:
    normalized_hint = f"{normalized_food_name} {food_name}".lower()
    compact_hint = normalized_hint.replace("-", "_").replace(" ", "_")

    if normalized_food_name in DIRECT_DRINK_NAMES:
        return True

    return any(keyword in normalized_hint or keyword in compact_hint for keyword in DRINK_KEYWORDS)


def resolve_nutrition_preset(
    *,
    food_name: str,
    normalized_food_name: str,
    canonical_food_name: str,
    nutrition_source: str,
    is_estimated: bool,
) -> ResolvedNutritionPreset:
    if canonical_food_name in NUTRITION_PRESETS and canonical_food_name != "generic_mixed_meal":
        return ResolvedNutritionPreset(
            canonical_food_name=canonical_food_name,
            nutrition_source=nutrition_source,
            is_estimated=is_estimated,
            preset=NUTRITION_PRESETS[canonical_food_name],
        )

    if is_packaged_drink(food_name=food_name, normalized_food_name=normalized_food_name):
        return ResolvedNutritionPreset(
            canonical_food_name="generic_unsweetened_drink",
            nutrition_source="drink_fallback",
            is_estimated=True,
            preset=NUTRITION_PRESETS["generic_unsweetened_drink"],
        )

    return ResolvedNutritionPreset(
        canonical_food_name=canonical_food_name,
        nutrition_source=nutrition_source,
        is_estimated=is_estimated,
        preset=NUTRITION_PRESETS[canonical_food_name],
    )


def resolve_portion(*, food_name: str, normalized_food_name: str, portion_unit: str, portion_value: Decimal, preset: NutritionPreset, ai_weight_g: Decimal | None = None) -> PortionResolution:
    source_portion_unit = portion_unit.strip()
    normalized_unit = normalize_portion_unit(source_portion_unit)
    normalized_value = quantize_decimal(portion_value)
    is_drink = is_packaged_drink(food_name=food_name, normalized_food_name=normalized_food_name)

    if is_drink:
        if normalized_unit == "ml" or normalized_unit == "cc":
            resolved_weight_g = normalized_value
            multiplier = quantize_decimal(resolved_weight_g / preset.portion_weight_g)
            return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "direct_milliliters", multiplier)

        if normalized_unit == "l":
            resolved_weight_g = quantize_decimal(normalized_value * Decimal("1000.00"))
            multiplier = quantize_decimal(resolved_weight_g / preset.portion_weight_g)
            return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "direct_milliliters", multiplier)

        if normalized_unit in DRINK_VOLUME_ML_BY_UNIT:
            resolved_weight_g = quantize_decimal(DRINK_VOLUME_ML_BY_UNIT[normalized_unit] * normalized_value)
            multiplier = quantize_decimal(resolved_weight_g / preset.portion_weight_g)
            method = "drink_serving_default" if normalized_unit == "serving" else "drink_container_default"
            return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, method, multiplier)

    if normalized_unit == "g":
        resolved_weight_g = normalized_value
        multiplier = quantize_decimal(resolved_weight_g / preset.portion_weight_g)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "direct_grams", multiplier)

    if normalized_unit == preset.portion_unit:
        resolved_weight_g = quantize_decimal(preset.portion_weight_g * normalized_value)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "exact_unit_match", normalized_value)

    for family_units in UNIT_FAMILIES.values():
        requested_weight = family_units.get(normalized_unit)
        canonical_weight = family_units.get(preset.portion_unit)
        if requested_weight is None or canonical_weight is None:
            continue

        ratio = quantize_decimal(requested_weight / canonical_weight)
        multiplier = quantize_decimal(normalized_value * ratio)
        resolved_weight_g = quantize_decimal(preset.portion_weight_g * multiplier)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "common_unit_conversion", multiplier)

    # 步驟 4b：AI 克重提示，僅限可數單位且總重在合理範圍內
    if normalized_unit in COUNTABLE_UNITS and ai_weight_g is not None:
        candidate_weight = quantize_decimal(ai_weight_g * normalized_value)
        if candidate_weight <= AI_WEIGHT_MAX_G:
            multiplier = quantize_decimal(candidate_weight / preset.portion_weight_g)
            return PortionResolution(source_portion_unit, normalized_unit, candidate_weight, "ai_weight_hint", multiplier)

    resolved_weight_g = quantize_decimal(preset.portion_weight_g * normalized_value)
    return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "assumed_common_serving_weight", normalized_value)
