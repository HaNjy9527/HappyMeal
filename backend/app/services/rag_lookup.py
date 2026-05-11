"""
V2-01-05：RAG 向量查詢服務

將食物名稱 embed 後，對 food_nutrition_embeddings 做 cosine 相似度查詢，
找出最接近的官方食物記錄。

設計原則：
    - lookup_rag_food 遇到任何 exception（無 API key、DB 不支援向量、逾時）
      都靜默 return None，讓 caller 退回 keyword catalog，不阻斷主流程。
    - SQLite 測試環境不支援 <=> 運算子，exception 自然觸發 fallback，
      無需修改現有測試。
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import FoodNutritionEmbedding

logger = logging.getLogger("app.rag_lookup")

EMBED_MODEL = "text-embedding-3-small"
COSINE_DISTANCE_THRESHOLD = 0.20   # distance < 0.20 ≈ cosine similarity > 0.80

_RAG_SQL = text("""
    SELECT
        id,
        display_name_zh,
        food_code,
        food_category,
        kcal_per_100g,
        protein_g_per_100g,
        fat_g_per_100g,
        carb_g_per_100g,
        embedding <=> CAST(:vec AS vector) AS distance
    FROM food_nutrition_embeddings
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> CAST(:vec AS vector)
    LIMIT 1
""")


def embed_food_query(text_input: str) -> list[float]:
    """呼叫 OpenAI embeddings API，返回 1536 維向量。"""
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.ai_food_api_key)
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text_input,
    )
    return response.data[0].embedding


def lookup_rag_food(
    food_name: str,
    normalized_food_name: str,
    db: Session,
    threshold: float = COSINE_DISTANCE_THRESHOLD,
) -> FoodNutritionEmbedding | None:
    """
    向量相似度查詢。

    Returns:
        FoodNutritionEmbedding 物件（只填 RAG 所需欄位），
        或 None（查無符合、threshold 未達、任何例外）。
    """
    try:
        query_text = f"{food_name} {normalized_food_name}".strip()
        query_vec = embed_food_query(query_text)
        vec_json = json.dumps(query_vec)

        row = db.execute(_RAG_SQL, {"vec": vec_json}).first()

        if row is None:
            return None

        if row.distance is None or row.distance >= threshold:
            logger.debug(
                "rag_lookup miss: food=%r distance=%.4f threshold=%.4f",
                food_name,
                row.distance if row.distance is not None else float("nan"),
                threshold,
            )
            return None

        logger.info(
            "rag_lookup hit: food=%r → %s (distance=%.4f)",
            food_name,
            row.display_name_zh,
            row.distance,
        )

        # 建構輕量 ORM 物件（只填 RAG 所需欄位，不走完整 ORM load）
        match = FoodNutritionEmbedding.__new__(FoodNutritionEmbedding)
        match.id = row.id
        match.display_name_zh = row.display_name_zh
        match.food_code = row.food_code
        match.food_category = row.food_category
        match.kcal_per_100g = row.kcal_per_100g
        match.protein_g_per_100g = row.protein_g_per_100g
        match.fat_g_per_100g = row.fat_g_per_100g
        match.carb_g_per_100g = row.carb_g_per_100g
        return match

    except Exception as exc:  # noqa: BLE001
        logger.debug("rag_lookup skipped (exception): %s: %s", type(exc).__name__, exc)
        return None
