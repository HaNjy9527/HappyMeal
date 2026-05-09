from decimal import Decimal

import pytest

from app.db.models import FoodAnalysisItem
from app.services.analysis_views import KCAL_ANOMALY_THRESHOLD, _is_item_anomalous, build_analysis_result_items


def make_item(kcal: Decimal, is_estimated: bool, **kwargs) -> FoodAnalysisItem:
    defaults = dict(
        food_name="Test Food",
        normalized_food_name="test_food",
        portion_value=Decimal("1.00"),
        portion_unit="portion",
        source_portion_unit=None,
        canonical_food_name="test_food",
        nutrition_source="default_fallback",
        resolved_weight_g=Decimal("200.00"),
        weight_estimation_method="default",
        confidence_score=None,
        protein_g=Decimal("10.00"),
        fat_g=Decimal("10.00"),
        carb_g=Decimal("10.00"),
    )
    defaults.update(kwargs)
    item = FoodAnalysisItem(**defaults, kcal=kcal, is_estimated=is_estimated)
    return item


class TestIsItemAnomalous:
    def test_estimated_above_threshold_is_anomalous(self):
        item = make_item(kcal=KCAL_ANOMALY_THRESHOLD + Decimal("1"), is_estimated=True)
        assert _is_item_anomalous(item) is True

    def test_estimated_at_threshold_is_not_anomalous(self):
        item = make_item(kcal=KCAL_ANOMALY_THRESHOLD, is_estimated=True)
        assert _is_item_anomalous(item) is False

    def test_estimated_below_threshold_is_not_anomalous(self):
        item = make_item(kcal=Decimal("800.00"), is_estimated=True)
        assert _is_item_anomalous(item) is False

    def test_official_source_above_threshold_is_not_anomalous(self):
        # official_source data should never be flagged even if high-calorie
        item = make_item(
            kcal=Decimal("2000.00"),
            is_estimated=False,
            nutrition_source="official_source",
        )
        assert _is_item_anomalous(item) is False

    def test_drink_fallback_above_threshold_is_anomalous(self):
        item = make_item(
            kcal=Decimal("1600.00"),
            is_estimated=True,
            nutrition_source="drink_fallback",
        )
        assert _is_item_anomalous(item) is True


class TestBuildAnalysisResultItems:
    def test_is_anomalous_propagated_in_result(self):
        item = make_item(kcal=Decimal("1800.00"), is_estimated=True)
        results = build_analysis_result_items([item])
        assert len(results) == 1
        assert results[0].is_anomalous is True

    def test_normal_item_is_not_anomalous(self):
        item = make_item(kcal=Decimal("500.00"), is_estimated=False)
        results = build_analysis_result_items([item])
        assert results[0].is_anomalous is False

    def test_metadata_fields_are_preserved(self):
        item = make_item(
            kcal=Decimal("300.00"),
            is_estimated=True,
            nutrition_source="default_fallback",
            canonical_food_name="generic_mixed_meal",
            resolved_weight_g=Decimal("250.00"),
            weight_estimation_method="default",
        )
        result = build_analysis_result_items([item])[0]
        assert result.nutrition_source == "default_fallback"
        assert result.canonical_food_name == "generic_mixed_meal"
        assert result.is_estimated is True
        assert result.resolved_weight_g == Decimal("250.00")
        assert result.weight_estimation_method == "default"
