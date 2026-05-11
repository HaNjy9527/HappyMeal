from __future__ import annotations

import re

from dataclasses import dataclass
from decimal import Decimal

from app.services.portion_resolution import NutritionPreset


@dataclass(frozen=True)
class OfficialNutritionRecord:
    canonical_food_name: str
    aliases: tuple[str, ...]
    preset: NutritionPreset
    source: str = "official_source"
    source_label: str = "curated_mvp_v1"


OFFICIAL_NUTRITION_CATALOG = {
    "black_coffee": OfficialNutritionRecord(
        canonical_food_name="black_coffee",
        aliases=("black_coffee", "americano", "unsweetened_coffee"),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("2.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.50"),
        ),
    ),
    "white_rice": OfficialNutritionRecord(
        canonical_food_name="white_rice",
        aliases=("white_rice", "generic_rice"),
        preset=NutritionPreset(
            "bowl",
            Decimal("160.00"),
            Decimal("216.00"),
            Decimal("5.00"),
            Decimal("1.80"),
            Decimal("45.00"),
        ),
    ),
    "boiled_egg": OfficialNutritionRecord(
        canonical_food_name="boiled_egg",
        aliases=("boiled_egg",),
        preset=NutritionPreset(
            "pcs",
            Decimal("50.00"),
            Decimal("78.00"),
            Decimal("6.50"),
            Decimal("5.30"),
            Decimal("0.60"),
        ),
    ),
    "chicken_breast": OfficialNutritionRecord(
        canonical_food_name="chicken_breast",
        aliases=("chicken_breast", "grilled_chicken_breast"),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("165.00"),
            Decimal("31.00"),
            Decimal("3.60"),
            Decimal("0.00"),
        ),
    ),
    "leafy_vegetables": OfficialNutritionRecord(
        canonical_food_name="leafy_vegetables",
        aliases=("leafy_vegetables",),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("35.00"),
            Decimal("2.00"),
            Decimal("0.50"),
            Decimal("6.00"),
        ),
    ),
    # --- 便當 ---
    "chicken_leg_bento": OfficialNutritionRecord(
        canonical_food_name="chicken_leg_bento",
        aliases=("chicken_leg_bento", "braised_chicken_leg_bento", "ji_tui_bian_dang"),
        preset=NutritionPreset("box", Decimal("650.00"), Decimal("750.00"), Decimal("32.00"), Decimal("22.00"), Decimal("95.00")),
    ),
    "pork_chop_bento": OfficialNutritionRecord(
        canonical_food_name="pork_chop_bento",
        aliases=("pork_chop_bento", "pai_gu_bian_dang", "pork_rib_bento"),
        preset=NutritionPreset("box", Decimal("650.00"), Decimal("800.00"), Decimal("30.00"), Decimal("28.00"), Decimal("95.00")),
    ),
    "braised_pork_bento": OfficialNutritionRecord(
        canonical_food_name="braised_pork_bento",
        aliases=("braised_pork_bento", "lu_rou_bian_dang", "minced_pork_bento"),
        preset=NutritionPreset("box", Decimal("600.00"), Decimal("750.00"), Decimal("26.00"), Decimal("25.00"), Decimal("90.00")),
    ),
    "fish_fillet_bento": OfficialNutritionRecord(
        canonical_food_name="fish_fillet_bento",
        aliases=("fish_fillet_bento", "yu_pai_bian_dang", "fish_bento"),
        preset=NutritionPreset("box", Decimal("600.00"), Decimal("680.00"), Decimal("28.00"), Decimal("18.00"), Decimal("90.00")),
    ),
    "vegetarian_bento": OfficialNutritionRecord(
        canonical_food_name="vegetarian_bento",
        aliases=("vegetarian_bento", "su_shi_bian_dang", "vegan_bento"),
        preset=NutritionPreset("box", Decimal("550.00"), Decimal("580.00"), Decimal("16.00"), Decimal("14.00"), Decimal("90.00")),
    ),
    # --- 飯類 ---
    "minced_pork_rice": OfficialNutritionRecord(
        canonical_food_name="minced_pork_rice",
        aliases=("minced_pork_rice", "lu_rou_fan", "braised_pork_rice", "braised_minced_pork_rice"),
        preset=NutritionPreset("bowl", Decimal("250.00"), Decimal("380.00"), Decimal("12.00"), Decimal("11.00"), Decimal("55.00")),
    ),
    "shredded_chicken_rice": OfficialNutritionRecord(
        canonical_food_name="shredded_chicken_rice",
        aliases=("shredded_chicken_rice", "ji_rou_fan"),
        preset=NutritionPreset("bowl", Decimal("250.00"), Decimal("320.00"), Decimal("14.00"), Decimal("6.00"), Decimal("52.00")),
    ),
    "pork_chop_rice": OfficialNutritionRecord(
        canonical_food_name="pork_chop_rice",
        aliases=("pork_chop_rice", "pai_gu_fan", "pork_rib_rice"),
        preset=NutritionPreset("plate", Decimal("380.00"), Decimal("580.00"), Decimal("24.00"), Decimal("18.00"), Decimal("78.00")),
    ),
    "fried_rice": OfficialNutritionRecord(
        canonical_food_name="fried_rice",
        aliases=("fried_rice", "chao_fan", "egg_fried_rice", "yangzhou_fried_rice"),
        preset=NutritionPreset("plate", Decimal("280.00"), Decimal("450.00"), Decimal("12.00"), Decimal("14.00"), Decimal("68.00")),
    ),
    "curry_rice": OfficialNutritionRecord(
        canonical_food_name="curry_rice",
        aliases=("curry_rice", "ka_li_fan", "japanese_curry_rice"),
        preset=NutritionPreset("plate", Decimal("380.00"), Decimal("550.00"), Decimal("18.00"), Decimal("14.00"), Decimal("85.00")),
    ),
    # --- 麵食 ---
    "beef_noodle_soup": OfficialNutritionRecord(
        canonical_food_name="beef_noodle_soup",
        aliases=("beef_noodle_soup", "niu_rou_mian", "taiwanese_beef_noodle"),
        preset=NutritionPreset("bowl", Decimal("650.00"), Decimal("620.00"), Decimal("30.00"), Decimal("18.00"), Decimal("85.00")),
    ),
    "plain_noodle_soup": OfficialNutritionRecord(
        canonical_food_name="plain_noodle_soup",
        aliases=("plain_noodle_soup", "tang_mian", "noodle_soup"),
        preset=NutritionPreset("bowl", Decimal("400.00"), Decimal("330.00"), Decimal("12.00"), Decimal("4.00"), Decimal("62.00")),
    ),
    "dan_zai_noodle": OfficialNutritionRecord(
        canonical_food_name="dan_zai_noodle",
        aliases=("dan_zai_noodle", "tan_tsai_noodle", "danzai_noodle"),
        preset=NutritionPreset("bowl", Decimal("350.00"), Decimal("290.00"), Decimal("14.00"), Decimal("6.00"), Decimal("48.00")),
    ),
    "dry_noodle": OfficialNutritionRecord(
        canonical_food_name="dry_noodle",
        aliases=("dry_noodle", "gan_mian", "sesame_noodle", "mixed_noodle"),
        preset=NutritionPreset("bowl", Decimal("250.00"), Decimal("400.00"), Decimal("12.00"), Decimal("14.00"), Decimal("57.00")),
    ),
    "rice_noodle_soup": OfficialNutritionRecord(
        canonical_food_name="rice_noodle_soup",
        aliases=("rice_noodle_soup", "mi_fen_tang", "rice_vermicelli_soup"),
        preset=NutritionPreset("bowl", Decimal("400.00"), Decimal("280.00"), Decimal("8.00"), Decimal("5.00"), Decimal("52.00")),
    ),
    "steamed_dumpling": OfficialNutritionRecord(
        canonical_food_name="steamed_dumpling",
        aliases=("steamed_dumpling", "jiao_zi", "boiled_dumpling", "water_dumpling"),
        preset=NutritionPreset("serving", Decimal("250.00"), Decimal("420.00"), Decimal("18.00"), Decimal("12.00"), Decimal("58.00")),
    ),
    "pan_fried_dumpling": OfficialNutritionRecord(
        canonical_food_name="pan_fried_dumpling",
        aliases=("pan_fried_dumpling", "guo_tie", "potsticker"),
        preset=NutritionPreset("serving", Decimal("180.00"), Decimal("380.00"), Decimal("14.00"), Decimal("16.00"), Decimal("48.00")),
    ),
    # --- 蛋白質 ---
    "chicken_leg": OfficialNutritionRecord(
        canonical_food_name="chicken_leg",
        aliases=("chicken_leg", "ji_tui", "braised_chicken_leg", "roasted_chicken_leg"),
        preset=NutritionPreset("pcs", Decimal("200.00"), Decimal("280.00"), Decimal("26.00"), Decimal("18.00"), Decimal("0.00")),
    ),
    "fried_chicken_cutlet": OfficialNutritionRecord(
        canonical_food_name="fried_chicken_cutlet",
        aliases=("fried_chicken_cutlet", "ji_pai", "chicken_steak", "taiwanese_chicken_cutlet"),
        preset=NutritionPreset("pcs", Decimal("200.00"), Decimal("460.00"), Decimal("28.00"), Decimal("24.00"), Decimal("30.00")),
    ),
    "pork_chop": OfficialNutritionRecord(
        canonical_food_name="pork_chop",
        aliases=("pork_chop", "pai_gu", "fried_pork_chop", "grilled_pork_chop"),
        preset=NutritionPreset("pcs", Decimal("180.00"), Decimal("360.00"), Decimal("26.00"), Decimal("22.00"), Decimal("12.00")),
    ),
    "braised_pork_belly": OfficialNutritionRecord(
        canonical_food_name="braised_pork_belly",
        aliases=("braised_pork_belly", "dong_po_rou", "hong_shao_rou", "red_braised_pork"),
        preset=NutritionPreset("serving", Decimal("150.00"), Decimal("380.00"), Decimal("18.00"), Decimal("28.00"), Decimal("8.00")),
    ),
    # --- 湯 ---
    "fish_ball_soup": OfficialNutritionRecord(
        canonical_food_name="fish_ball_soup",
        aliases=("fish_ball_soup", "yu_wan_tang", "fishball_soup"),
        preset=NutritionPreset("bowl", Decimal("350.00"), Decimal("180.00"), Decimal("12.00"), Decimal("6.00"), Decimal("18.00")),
    ),
    "egg_drop_soup": OfficialNutritionRecord(
        canonical_food_name="egg_drop_soup",
        aliases=("egg_drop_soup", "dan_hua_tang", "egg_flower_soup"),
        preset=NutritionPreset("bowl", Decimal("300.00"), Decimal("80.00"), Decimal("6.00"), Decimal("4.00"), Decimal("4.00")),
    ),
    "radish_pork_rib_soup": OfficialNutritionRecord(
        canonical_food_name="radish_pork_rib_soup",
        aliases=("radish_pork_rib_soup", "luo_bo_pai_gu_tang", "daikon_pork_rib_soup"),
        preset=NutritionPreset("bowl", Decimal("380.00"), Decimal("260.00"), Decimal("18.00"), Decimal("14.00"), Decimal("14.00")),
    ),
    "miso_soup": OfficialNutritionRecord(
        canonical_food_name="miso_soup",
        aliases=("miso_soup", "wei_zeng_tang", "japanese_miso_soup"),
        preset=NutritionPreset("bowl", Decimal("250.00"), Decimal("55.00"), Decimal("3.00"), Decimal("2.00"), Decimal("5.00")),
    ),
    # --- 配菜 ---
    "braised_egg": OfficialNutritionRecord(
        canonical_food_name="braised_egg",
        aliases=("braised_egg", "lu_dan", "soy_braised_egg", "marinated_egg"),
        preset=NutritionPreset("pcs", Decimal("60.00"), Decimal("95.00"), Decimal("7.00"), Decimal("6.00"), Decimal("2.00")),
    ),
    "tofu": OfficialNutritionRecord(
        canonical_food_name="tofu",
        aliases=("tofu", "bean_curd", "soft_tofu", "firm_tofu", "dou_fu"),
        preset=NutritionPreset("g", Decimal("100.00"), Decimal("76.00"), Decimal("8.00"), Decimal("4.00"), Decimal("2.00")),
    ),
    "braised_tofu": OfficialNutritionRecord(
        canonical_food_name="braised_tofu",
        aliases=("braised_tofu", "lu_dou_fu", "soy_braised_tofu"),
        preset=NutritionPreset("serving", Decimal("150.00"), Decimal("140.00"), Decimal("12.00"), Decimal("7.00"), Decimal("8.00")),
    ),
    "pig_blood_cake": OfficialNutritionRecord(
        canonical_food_name="pig_blood_cake",
        aliases=("pig_blood_cake", "zhu_xue_gao", "pigs_blood_cake"),
        preset=NutritionPreset("serving", Decimal("100.00"), Decimal("200.00"), Decimal("8.00"), Decimal("2.00"), Decimal("38.00")),
    ),
    "stir_fried_morning_glory": OfficialNutritionRecord(
        canonical_food_name="stir_fried_morning_glory",
        aliases=("stir_fried_morning_glory", "kong_xin_cai", "water_spinach", "fried_water_spinach"),
        preset=NutritionPreset("g", Decimal("100.00"), Decimal("65.00"), Decimal("2.00"), Decimal("4.00"), Decimal("5.00")),
    ),
    "stir_fried_cabbage": OfficialNutritionRecord(
        canonical_food_name="stir_fried_cabbage",
        aliases=("stir_fried_cabbage", "chao_gao_li_cai", "fried_cabbage"),
        preset=NutritionPreset("g", Decimal("100.00"), Decimal("55.00"), Decimal("2.00"), Decimal("3.00"), Decimal("5.00")),
    ),
    # --- 飲料 ---
    "unsweetened_soy_milk": OfficialNutritionRecord(
        canonical_food_name="unsweetened_soy_milk",
        aliases=("unsweetened_soy_milk", "wu_tang_dou_jiang", "plain_soy_milk"),
        preset=NutritionPreset("cup", Decimal("250.00"), Decimal("70.00"), Decimal("5.00"), Decimal("3.00"), Decimal("5.00")),
    ),
    "sweetened_soy_milk": OfficialNutritionRecord(
        canonical_food_name="sweetened_soy_milk",
        aliases=("sweetened_soy_milk", "tian_dou_jiang", "soy_milk"),
        preset=NutritionPreset("cup", Decimal("250.00"), Decimal("120.00"), Decimal("5.00"), Decimal("3.00"), Decimal("18.00")),
    ),
    "rice_milk": OfficialNutritionRecord(
        canonical_food_name="rice_milk",
        aliases=("rice_milk", "mi_jiang", "taiwanese_rice_milk"),
        preset=NutritionPreset("cup", Decimal("250.00"), Decimal("180.00"), Decimal("2.00"), Decimal("4.00"), Decimal("33.00")),
    ),
    "bubble_milk_tea": OfficialNutritionRecord(
        canonical_food_name="bubble_milk_tea",
        aliases=("bubble_milk_tea", "boba_milk_tea", "pearl_milk_tea", "zhen_zhu_nai_cha"),
        preset=NutritionPreset("cup", Decimal("500.00"), Decimal("400.00"), Decimal("3.00"), Decimal("5.00"), Decimal("85.00")),
    ),
}


def normalize_catalog_hint(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[_\-]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized)


def lookup_official_nutrition(
    *,
    food_name: str,
    normalized_food_name: str,
    canonical_food_name: str | None = None,
) -> OfficialNutritionRecord | None:
    direct_keys = (normalized_food_name, canonical_food_name)
    for key in direct_keys:
        if key and key in OFFICIAL_NUTRITION_CATALOG:
            return OFFICIAL_NUTRITION_CATALOG[key]

    hints = {
        normalize_catalog_hint(food_name),
        normalize_catalog_hint(normalized_food_name),
    }
    if canonical_food_name:
        hints.add(normalize_catalog_hint(canonical_food_name))

    for record in OFFICIAL_NUTRITION_CATALOG.values():
        alias_hints = {normalize_catalog_hint(alias) for alias in record.aliases}
        if hints & alias_hints:
            return record

    return None
