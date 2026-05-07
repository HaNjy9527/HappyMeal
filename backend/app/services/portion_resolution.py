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


def resolve_portion(*, food_name: str, normalized_food_name: str, portion_unit: str, portion_value: Decimal, preset: NutritionPreset) -> PortionResolution:
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

    resolved_weight_g = quantize_decimal(preset.portion_weight_g * normalized_value)
    return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "assumed_common_serving_weight", normalized_value)
