"""
V2-01-03：衛福部食品營養成分資料庫 2025 版 Excel 匯入腳本

此腳本為一次性 import，將 Excel 中 2503 筆食物資料寫入 food_nutrition_embeddings 表。
embedding 欄位保持 NULL，待 V2-01-04 再呼叫 OpenAI embeddings API 填入。

使用方式（在 backend/ 目錄下執行）：

    uv run python scripts/import_nutrition_xlsx.py --xlsx ../docs/食品營養成分資料庫2025版UPDATE1EXCEL(另開新視窗).xlsx

前置條件：
    - V2-01-01 migration 已跑（pgvector + food_nutrition_embeddings 表存在）
    - V2-01-02 migration 已跑（food_code, food_category, nutrients_json 欄位存在）
    - DATABASE_URL 環境變數已設定（或 .env 在 backend/ 目錄）
    - openpyxl 已安裝：uv pip install openpyxl
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import openpyxl

# 讓 script 能找到 app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.models import FoodNutritionEmbedding  # noqa: E402
from app.db.session import get_engine, get_session_factory  # noqa: E402

# --- 欄位索引（0-based，對應 Excel Row 2 header）---
COL_FOOD_CODE = 0        # 整合編號
COL_FOOD_CATEGORY = 1    # 食品分類
COL_FOOD_NAME_ZH = 2     # 樣品名稱
COL_DESCRIPTION = 3      # 內容物描述
COL_ALIASES = 4          # 俗名
COL_KCAL = 7             # 修正熱量(kcal)  ← 用這個，非 col 6 的熱量
COL_PROTEIN = 9          # 粗蛋白(g)
COL_FAT = 10             # 粗脂肪(g)
COL_CARB = 13            # 總碳水化合物(g)

TOTAL_DATA_COLS = 110    # 第 111 欄是 None，不取


def to_decimal(value: object) -> Decimal | None:
    """將 Excel 儲存格值轉為 Decimal，None / 空白 / '*' 回傳 None。"""
    if value is None or value == "" or value == "*":
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def to_str(value: object) -> str:
    """將 Excel 儲存格值轉為 str，None 回傳空字串。"""
    if value is None:
        return ""
    return str(value).strip()


def make_embed_text(food_category: str, food_name_zh: str, aliases_raw: str) -> str:
    """
    產生用於 embedding 的文字。
    格式：{食品分類} {樣品名稱} {俗名1} {俗名2} ...

    範例：
        "穀物類 大麥仁 小薏仁 洋薏仁 珍珠薏仁"
        "穀物類 大麥片"
    """
    parts = [p for p in [food_category, food_name_zh] if p]
    if aliases_raw:
        for alias in aliases_raw.split(","):
            alias = alias.strip()
            if alias and alias not in parts:
                parts.append(alias)
    return " ".join(parts)


def build_nutrients_json(headers: list[str | None], row: tuple) -> dict:
    """
    把整列 110 欄資料打包成 dict，存入 nutrients_json。
    - 數字欄位：保留為 float（JSON 相容）
    - 字串欄位（如 P/M/S 比例）：保留為 str
    - None / 空白：存 None
    """
    result: dict[str, object] = {}
    for i, header in enumerate(headers):
        if i >= TOTAL_DATA_COLS:
            break
        if not header:
            continue
        value = row[i] if i < len(row) else None
        if isinstance(value, (int, float)):
            result[header] = value
        elif isinstance(value, str) and value.strip():
            result[header] = value.strip()
        else:
            result[header] = None
    return result


def import_xlsx(xlsx_path: Path) -> None:
    from sqlalchemy.orm import Session

    engine = get_engine()
    session_factory = get_session_factory()
    db: Session = session_factory(bind=engine)

    try:
        print(f"Opening: {xlsx_path}")
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active

        all_rows = list(ws.iter_rows(min_row=2, values_only=True))
        headers: list[str | None] = list(all_rows[0])
        data_rows = all_rows[1:]

        print(f"Headers: {len(headers)} columns")
        print(f"Data rows: {len(data_rows)}")
        print()

        inserted = updated = skipped = errors = 0

        for i, row in enumerate(data_rows):
            try:
                food_code = to_str(row[COL_FOOD_CODE])
                food_category = to_str(row[COL_FOOD_CATEGORY])
                food_name_zh = to_str(row[COL_FOOD_NAME_ZH])
                aliases_raw = to_str(row[COL_ALIASES])

                if not food_code or not food_name_zh:
                    skipped += 1
                    continue

                kcal = to_decimal(row[COL_KCAL])
                protein = to_decimal(row[COL_PROTEIN])
                fat = to_decimal(row[COL_FAT])
                carb = to_decimal(row[COL_CARB])

                embed_text = make_embed_text(food_category, food_name_zh, aliases_raw)
                nutrients = build_nutrients_json(headers, row)

                # UPSERT on food_code
                existing = db.query(FoodNutritionEmbedding).filter_by(food_code=food_code).first()

                if existing:
                    existing.food_category = food_category or None
                    existing.display_name_zh = food_name_zh
                    existing.embed_text = embed_text
                    existing.kcal_per_100g = kcal or Decimal("0")
                    existing.protein_g_per_100g = protein or Decimal("0")
                    existing.fat_g_per_100g = fat or Decimal("0")
                    existing.carb_g_per_100g = carb or Decimal("0")
                    existing.nutrients_json = nutrients
                    updated += 1
                else:
                    # canonical_food_name 用 food_code 確保唯一性（display 用 display_name_zh）
                    record = FoodNutritionEmbedding(
                        canonical_food_name=food_code,
                        food_code=food_code,
                        food_category=food_category or None,
                        display_name_zh=food_name_zh,
                        embed_text=embed_text,
                        kcal_per_100g=kcal or Decimal("0"),
                        protein_g_per_100g=protein or Decimal("0"),
                        fat_g_per_100g=fat or Decimal("0"),
                        carb_g_per_100g=carb or Decimal("0"),
                        nutrients_json=nutrients,
                        source="official",
                    )
                    db.add(record)
                    inserted += 1

                # 每 200 筆 flush 一次，避免記憶體過大
                if (i + 1) % 200 == 0:
                    db.flush()
                    print(f"  [{i + 1}/{len(data_rows)}] inserted={inserted} updated={updated} skipped={skipped}")

            except Exception as exc:
                print(f"  Row {i + 3}: ERROR — {exc}")
                errors += 1

        db.commit()
        wb.close()

        print()
        print("=" * 50)
        print(f"完成")
        print(f"  inserted : {inserted}")
        print(f"  updated  : {updated}")
        print(f"  skipped  : {skipped}")
        print(f"  errors   : {errors}")
        print(f"  total    : {inserted + updated + skipped + errors}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="匯入衛福部食品營養成分資料庫 Excel")
    parser.add_argument("--xlsx", required=True, help="Excel 檔案路徑")
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx)
    if not xlsx_path.exists():
        print(f"找不到檔案：{xlsx_path}", file=sys.stderr)
        sys.exit(1)

    import_xlsx(xlsx_path)


if __name__ == "__main__":
    main()
