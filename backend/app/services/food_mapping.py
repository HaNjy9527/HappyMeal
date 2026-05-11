from __future__ import annotations

import re

from dataclasses import dataclass
from typing import Literal


MatchType = Literal["direct", "alias", "keyword", "default_fallback"]

CANONICAL_FOOD_KEYS = frozenset(
    {
        "chicken_salad",
        "boiled_egg",
        "grilled_chicken_rice",
        "stir_fried_vegetables",
        "grilled_salmon",
        "brown_rice",
        "steamed_broccoli",
        "generic_mixed_meal",
        "generic_rice",
        "generic_vegetables",
        "generic_condiment",
        "generic_garnish",
        "generic_protein",
        # 便當
        "chicken_leg_bento",
        "pork_chop_bento",
        "braised_pork_bento",
        "fish_fillet_bento",
        "vegetarian_bento",
        # 飯類
        "minced_pork_rice",
        "shredded_chicken_rice",
        "pork_chop_rice",
        "fried_rice",
        "curry_rice",
        # 麵食
        "beef_noodle_soup",
        "plain_noodle_soup",
        "dan_zai_noodle",
        "dry_noodle",
        "rice_noodle_soup",
        "steamed_dumpling",
        "pan_fried_dumpling",
        # 蛋白質
        "chicken_leg",
        "fried_chicken_cutlet",
        "pork_chop",
        "braised_pork_belly",
        # 湯
        "fish_ball_soup",
        "egg_drop_soup",
        "radish_pork_rib_soup",
        "miso_soup",
        # 配菜
        "braised_egg",
        "tofu",
        "braised_tofu",
        "pig_blood_cake",
        "stir_fried_morning_glory",
        "stir_fried_cabbage",
        # 飲料
        "unsweetened_soy_milk",
        "sweetened_soy_milk",
        "rice_milk",
        "bubble_milk_tea",
        # 輕食 / 早餐
        "oatmeal",
        "greek_yogurt",
        "avocado_toast",
        "sandwich",
        "rice_ball",
        "tuna_salad",
        # 水果
        "banana",
        "apple",
        "mixed_fruits",
        # 咖啡 / 飲品
        "latte",
        "matcha_latte",
        "fruit_smoothie",
        # 台灣常見輕食
        "spring_roll",
        "congee",
    }
)

ALIAS_MAPPING = {
    "chicken_rice_bowl": "generic_mixed_meal",
    "white_rice": "generic_rice",
    "cabbage": "generic_vegetables",
    "ginger_shreds": "generic_garnish",
    "chili_sauce": "generic_condiment",
    # 便當 aliases
    "braised_chicken_leg_bento": "chicken_leg_bento",
    "lu_rou_bian_dang": "braised_pork_bento",
    "pai_gu_bian_dang": "pork_chop_bento",
    "yu_pai_bian_dang": "fish_fillet_bento",
    # 飯類 aliases
    "lu_rou_fan": "minced_pork_rice",
    "braised_pork_rice": "minced_pork_rice",
    "braised_minced_pork_rice": "minced_pork_rice",
    "ji_rou_fan": "shredded_chicken_rice",
    "pai_gu_fan": "pork_chop_rice",
    "chao_fan": "fried_rice",
    "egg_fried_rice": "fried_rice",
    "yangzhou_fried_rice": "fried_rice",
    "ka_li_fan": "curry_rice",
    "japanese_curry_rice": "curry_rice",
    # 麵食 aliases
    "niu_rou_mian": "beef_noodle_soup",
    "taiwanese_beef_noodle": "beef_noodle_soup",
    "tang_mian": "plain_noodle_soup",
    "noodle_soup": "plain_noodle_soup",
    "gan_mian": "dry_noodle",
    "sesame_noodle": "dry_noodle",
    "mixed_noodle": "dry_noodle",
    "mi_fen_tang": "rice_noodle_soup",
    "rice_vermicelli_soup": "rice_noodle_soup",
    "jiao_zi": "steamed_dumpling",
    "boiled_dumpling": "steamed_dumpling",
    "guo_tie": "pan_fried_dumpling",
    "potsticker": "pan_fried_dumpling",
    # 蛋白質 aliases
    "ji_tui": "chicken_leg",
    "braised_chicken_leg": "chicken_leg",
    "roasted_chicken_leg": "chicken_leg",
    "ji_pai": "fried_chicken_cutlet",
    "chicken_steak": "fried_chicken_cutlet",
    "taiwanese_chicken_cutlet": "fried_chicken_cutlet",
    "pai_gu": "pork_chop",
    "fried_pork_chop": "pork_chop",
    "dong_po_rou": "braised_pork_belly",
    "hong_shao_rou": "braised_pork_belly",
    "red_braised_pork": "braised_pork_belly",
    # 湯 aliases
    "yu_wan_tang": "fish_ball_soup",
    "fishball_soup": "fish_ball_soup",
    "dan_hua_tang": "egg_drop_soup",
    "egg_flower_soup": "egg_drop_soup",
    "luo_bo_pai_gu_tang": "radish_pork_rib_soup",
    "daikon_pork_rib_soup": "radish_pork_rib_soup",
    "wei_zeng_tang": "miso_soup",
    # 配菜 aliases
    "lu_dan": "braised_egg",
    "soy_braised_egg": "braised_egg",
    "marinated_egg": "braised_egg",
    "bean_curd": "tofu",
    "dou_fu": "tofu",
    "lu_dou_fu": "braised_tofu",
    "soy_braised_tofu": "braised_tofu",
    "zhu_xue_gao": "pig_blood_cake",
    "kong_xin_cai": "stir_fried_morning_glory",
    "water_spinach": "stir_fried_morning_glory",
    "chao_gao_li_cai": "stir_fried_cabbage",
    "fried_cabbage": "stir_fried_cabbage",
    # 飲料 aliases
    "wu_tang_dou_jiang": "unsweetened_soy_milk",
    "plain_soy_milk": "unsweetened_soy_milk",
    "tian_dou_jiang": "sweetened_soy_milk",
    "soy_milk": "sweetened_soy_milk",
    "mi_jiang": "rice_milk",
    "boba_milk_tea": "bubble_milk_tea",
    "pearl_milk_tea": "bubble_milk_tea",
    "zhen_zhu_nai_cha": "bubble_milk_tea",
    # 輕食 / 早餐 aliases
    "oat_porridge": "oatmeal",
    "rolled_oats": "oatmeal",
    "overnight_oats": "oatmeal",
    "plain_yogurt": "greek_yogurt",
    "yogurt": "greek_yogurt",
    "avocado_on_toast": "avocado_toast",
    "whole_wheat_sandwich": "sandwich",
    "club_sandwich": "sandwich",
    "onigiri": "rice_ball",
    "taiwan_rice_ball": "rice_ball",
    "tuna_vegetable_salad": "tuna_salad",
    # 水果 aliases
    "fruit_salad": "mixed_fruits",
    "fruit_plate": "mixed_fruits",
    "fruit_platter": "mixed_fruits",
    # 咖啡 / 飲品 aliases
    "cafe_latte": "latte",
    "flat_white": "latte",
    "green_tea_latte": "matcha_latte",
    "matcha_milk": "matcha_latte",
    "smoothie": "fruit_smoothie",
    "fruit_shake": "fruit_smoothie",
    "berry_smoothie": "fruit_smoothie",
    # 台灣常見輕食 aliases
    "popiah": "spring_roll",
    "taiwanese_spring_roll": "spring_roll",
    "fresh_spring_roll": "spring_roll",
    "rice_congee": "congee",
    "plain_congee": "congee",
    "white_congee": "congee",
}

KEYWORD_RULES = [
    ("generic_condiment", ("sauce", "dressing", "dip", "醬", "醬汁")),
    ("generic_garnish", ("ginger", "scallion", "garlic", "sesame", "薑", "蔥", "蒜", "芝麻")),
    # 特定飲品（先於通用規則）
    ("matcha_latte", ("matcha", "抹茶")),
    ("latte", ("latte",)),
    ("fruit_smoothie", ("smoothie", "果昔")),
    ("bubble_milk_tea", ("boba", "bubble tea", "pearl milk", "珍珠奶茶", "珍奶")),
    # 特定食物（先於通用規則）
    ("oatmeal", ("oatmeal", "燕麥粥")),
    ("greek_yogurt", ("yogurt", "優格")),
    ("spring_roll", ("spring roll", "潤餅", "popiah")),
    ("mixed_fruits", ("fruit platter", "fruit bowl", "fruit plate", "水果拼盤", "水果切盤", "水果盤")),
    ("miso_soup", ("miso", "味噌")),
    ("beef_noodle_soup", ("beef noodle", "牛肉麵")),
    ("fried_rice", ("fried rice", "炒飯")),
    ("steamed_dumpling", ("dumpling", "水餃", "餃子")),
    ("pan_fried_dumpling", ("potsticker", "鍋貼")),
    ("minced_pork_rice", ("lu rou fan", "滷肉飯")),
    ("braised_egg", ("braised egg", "滷蛋", "lu dan")),
    ("boiled_egg", ("egg", "omelette", "蛋", "水煮蛋", "荷包蛋")),
    ("generic_vegetables", ("vegetable", "broccoli", "cabbage", "lettuce", "greens", "高麗菜", "青菜", "花椰菜", "蔬菜")),
    ("generic_rice", ("rice", "porridge", "grain", "飯", "粥", "穀")),
    ("generic_protein", ("chicken", "beef", "pork", "tofu", "salmon", "fish", "shrimp", "雞", "牛", "豬", "豆腐", "魚", "蝦")),
    ("generic_mixed_meal", ("bento", "meal", "curry", "noodle", "pasta", "便當", "套餐", "燴飯", "麵")),
]

NUTRITION_SOURCE_BY_MATCH_TYPE: dict[MatchType, str] = {
    "direct": "preset",
    "alias": "alias_mapping",
    "keyword": "keyword_fallback",
    "default_fallback": "default_fallback",
}


@dataclass(frozen=True)
class CanonicalFoodMappingResult:
    canonical_food_name: str
    match_type: MatchType
    matched_term: str
    is_estimated: bool


def normalize_food_hint(food_name: str, normalized_food_name: str) -> str:
    food_hint = f"{normalized_food_name} {food_name}".lower()
    return re.sub(r"[_\-]+", " ", food_hint)


def find_matching_keyword(compact_food_hint: str, keywords: tuple[str, ...]) -> str | None:
    for keyword in keywords:
        if keyword in compact_food_hint:
            return keyword
    return None


def resolve_canonical_food(*, food_name: str, normalized_food_name: str) -> CanonicalFoodMappingResult:
    if normalized_food_name in CANONICAL_FOOD_KEYS:
        return CanonicalFoodMappingResult(
            canonical_food_name=normalized_food_name,
            match_type="direct",
            matched_term=normalized_food_name,
            is_estimated=False,
        )

    aliased_food_name = ALIAS_MAPPING.get(normalized_food_name)
    if aliased_food_name is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name=aliased_food_name,
            match_type="alias",
            matched_term=normalized_food_name,
            is_estimated=True,
        )

    compact_food_hint = normalize_food_hint(food_name, normalized_food_name)
    keyword_map = dict(KEYWORD_RULES)

    condiment_match = find_matching_keyword(compact_food_hint, keyword_map["generic_condiment"])
    if condiment_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_condiment",
            match_type="keyword",
            matched_term=condiment_match,
            is_estimated=True,
        )

    garnish_match = find_matching_keyword(compact_food_hint, keyword_map["generic_garnish"])
    if garnish_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_garnish",
            match_type="keyword",
            matched_term=garnish_match,
            is_estimated=True,
        )

    egg_match = find_matching_keyword(compact_food_hint, keyword_map["boiled_egg"])
    if egg_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="boiled_egg",
            match_type="keyword",
            matched_term=egg_match,
            is_estimated=True,
        )

    rice_match = find_matching_keyword(compact_food_hint, keyword_map["generic_rice"])
    protein_match = find_matching_keyword(compact_food_hint, keyword_map["generic_protein"])
    meal_match = find_matching_keyword(compact_food_hint, keyword_map["generic_mixed_meal"])

    if rice_match is not None and protein_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_mixed_meal",
            match_type="keyword",
            matched_term=f"{rice_match}+{protein_match}",
            is_estimated=True,
        )

    if meal_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_mixed_meal",
            match_type="keyword",
            matched_term=meal_match,
            is_estimated=True,
        )

    vegetables_match = find_matching_keyword(compact_food_hint, keyword_map["generic_vegetables"])
    if vegetables_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_vegetables",
            match_type="keyword",
            matched_term=vegetables_match,
            is_estimated=True,
        )

    if rice_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_rice",
            match_type="keyword",
            matched_term=rice_match,
            is_estimated=True,
        )

    if protein_match is not None:
        return CanonicalFoodMappingResult(
            canonical_food_name="generic_protein",
            match_type="keyword",
            matched_term=protein_match,
            is_estimated=True,
        )

    return CanonicalFoodMappingResult(
        canonical_food_name="generic_mixed_meal",
        match_type="default_fallback",
        matched_term="generic_mixed_meal",
        is_estimated=True,
    )
