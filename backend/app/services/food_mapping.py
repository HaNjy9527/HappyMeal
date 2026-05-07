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
    }
)

ALIAS_MAPPING = {
    "chicken_rice_bowl": "generic_mixed_meal",
    "white_rice": "generic_rice",
    "cabbage": "generic_vegetables",
    "ginger_shreds": "generic_garnish",
    "chili_sauce": "generic_condiment",
}

KEYWORD_RULES = [
    ("generic_condiment", ("sauce", "dressing", "dip", "醬", "醬汁")),
    ("generic_garnish", ("ginger", "scallion", "garlic", "sesame", "薑", "蔥", "蒜", "芝麻")),
    ("boiled_egg", ("egg", "omelette", "蛋", "水煮蛋", "荷包蛋")),
    ("generic_vegetables", ("vegetable", "broccoli", "cabbage", "lettuce", "greens", "高麗菜", "青菜", "花椰菜", "蔬菜")),
    ("generic_rice", ("rice", "porridge", "grain", "飯", "粥", "穀")),
    ("generic_protein", ("chicken", "beef", "pork", "tofu", "salmon", "fish", "shrimp", "雞", "牛", "豬", "豆腐", "魚", "蝦")),
    ("generic_mixed_meal", ("bento", "meal", "curry", "noodle", "pasta", "便當", "套餐", "炒飯", "燴飯", "麵")),
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
