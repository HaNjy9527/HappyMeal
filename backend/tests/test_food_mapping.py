import json
from decimal import Decimal

from app.services.food_mapping import resolve_canonical_food
from app.services.recognition_openai import parse_openai_candidate
from app.services.recognition_normalization import normalize_provider_candidates
from app.services.recognition_provider import ProviderCandidate


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


# --- food_type hint 測試 ---

def test_resolve_canonical_food_uses_food_type_hint_for_condiment():
    """wasabi 沒有關鍵字規則，但 food_type="condiment" 應直接命中 generic_condiment。"""
    result = resolve_canonical_food(
        food_name="哇沙比",
        normalized_food_name="wasabi",
        food_type="condiment",
    )

    assert result.canonical_food_name == "generic_condiment"
    assert result.match_type == "food_type_hint"
    assert result.matched_term == "condiment"
    assert result.is_estimated is True


def test_resolve_canonical_food_food_type_hint_overrides_keyword():
    """food_type hint 優先於關鍵字：wasabi 含蛋白質字詞不在 keyword，
    但 food_type="grain" 應直接命中 generic_rice，而非走 default_fallback。"""
    result = resolve_canonical_food(
        food_name="哇沙比",
        normalized_food_name="wasabi",
        food_type="grain",
    )

    assert result.canonical_food_name == "generic_rice"
    assert result.match_type == "food_type_hint"


def test_resolve_canonical_food_food_type_hint_skips_when_unknown_type():
    """未知的 food_type 應直接進入 keyword 掃描，不應中斷或 fallback。
    使用沒有 alias 的 normalized_food_name 以確保走 keyword 路徑。"""
    result = resolve_canonical_food(
        food_name="辣椒醬",
        normalized_food_name="mystery_hot_sauce",   # 不在 ALIAS_MAPPING
        food_type="unknown_category",
    )

    # 應走 keyword 命中 generic_condiment（含「醬」）
    assert result.canonical_food_name == "generic_condiment"
    assert result.match_type == "keyword"


def test_resolve_canonical_food_food_type_hint_skips_when_none():
    """food_type=None 不影響既有邏輯。"""
    result = resolve_canonical_food(
        food_name="哇沙比",
        normalized_food_name="wasabi",
        food_type=None,
    )

    # 沒有 food_type，wasabi 沒有關鍵字規則 → default_fallback
    assert result.canonical_food_name == "generic_mixed_meal"
    assert result.match_type == "default_fallback"


# --- parse_openai_candidate food_type 解析測試 ---

def test_parse_openai_candidate_extracts_food_type():
    """parse_openai_candidate 應正確解析 food_type 欄位。"""
    payload = {
        "food_name": "哇沙比",
        "normalized_food_name": "wasabi",
        "food_type": "condiment",
        "confidence_score": 0.80,
        "portion_default": 1,
        "portion_unit": "tbsp",
    }
    candidate = parse_openai_candidate(payload)

    assert candidate is not None
    assert candidate.food_type == "condiment"


def test_parse_openai_candidate_food_type_defaults_to_none_when_missing():
    """food_type 欄位缺失時應為 None，不應拋出例外。"""
    payload = {
        "food_name": "白米飯",
        "normalized_food_name": "white_rice",
        "confidence_score": 0.90,
        "portion_default": 1,
        "portion_unit": "bowl",
    }
    candidate = parse_openai_candidate(payload)

    assert candidate is not None
    assert candidate.food_type is None


# --- normalize_provider_candidates food_type 傳遞測試 ---

def test_normalize_provider_candidates_passes_through_food_type():
    """正規化後 food_type 應保留。"""
    candidates = [
        ProviderCandidate(
            food_name="哇沙比",
            normalized_food_name="wasabi",
            confidence_score=Decimal("0.80"),
            portion_default=Decimal("1.00"),
            portion_unit="tbsp",
            food_type="condiment",
        ),
        ProviderCandidate(
            food_name="白米飯",
            normalized_food_name="white_rice",
            confidence_score=Decimal("0.90"),
            portion_default=Decimal("1.00"),
            portion_unit="bowl",
            food_type=None,
        ),
    ]

    result = normalize_provider_candidates(candidates)

    assert len(result) == 2
    assert result[0].food_type == "condiment"
    assert result[1].food_type is None
