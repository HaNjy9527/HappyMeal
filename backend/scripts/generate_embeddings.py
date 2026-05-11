"""
V2-01-04：批次生成 food_nutrition_embeddings 向量

對 embedding IS NULL 的列呼叫 OpenAI text-embedding-3-small API，
將 1536 維向量寫入 DB。腳本支援斷點重跑（已有向量的列會跳過）。

使用方式（在 backend/ 目錄下執行）：

    uv run python scripts/generate_embeddings.py

前置條件：
    - V2-01-03 import 已跑（food_nutrition_embeddings 表有 2503 筆資料）
    - DATABASE_URL 環境變數已設定（或 .env 在 backend/ 目錄）
    - AI_API_KEY 環境變數已設定
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# 讓 script 能找到 app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.models import FoodNutritionEmbedding  # noqa: E402
from app.db.session import get_engine, get_session_factory  # noqa: E402

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100          # OpenAI 每次最多 2048，取 100 保守安全
SLEEP_BETWEEN_BATCHES = 0.5  # 秒，避免觸發 rate limit


def generate_embeddings() -> None:
    from sqlalchemy.orm import Session

    settings = get_settings()
    if not settings.ai_food_api_key:
        print("ERROR：未設定 AI_API_KEY 環境變數", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=settings.ai_food_api_key)
    engine = get_engine()
    session_factory = get_session_factory()
    db: Session = session_factory(bind=engine)

    try:
        # 查詢所有尚未有向量的列，依 id 排序確保每次順序一致
        pending: list[FoodNutritionEmbedding] = (
            db.query(FoodNutritionEmbedding)
            .filter(FoodNutritionEmbedding.embedding.is_(None))
            .order_by(FoodNutritionEmbedding.id)
            .all()
        )

        total = len(pending)
        print(f"待生成向量：{total} 筆")

        if total == 0:
            print("所有列已有向量，無需處理。")
            return

        written = 0

        for batch_start in range(0, total, BATCH_SIZE):
            batch = pending[batch_start : batch_start + BATCH_SIZE]
            texts = [row.embed_text for row in batch]

            response = client.embeddings.create(
                model=EMBED_MODEL,
                input=texts,
            )

            for i, row in enumerate(batch):
                row.embedding = response.data[i].embedding

            db.commit()
            written += len(batch)
            print(f"  [{written}/{total}] done")

            if batch_start + BATCH_SIZE < total:
                time.sleep(SLEEP_BETWEEN_BATCHES)

        print()
        print("=" * 40)
        print(f"完成：{written} 筆向量已寫入")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_embeddings()
