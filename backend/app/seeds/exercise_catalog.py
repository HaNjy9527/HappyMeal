from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models import ExerciseCatalog
from app.db.session import get_engine, get_session_factory


EXERCISE_SEED_DATA = [
    {"name": "Brisk Walking", "category": "cardio", "met_value": Decimal("4.30"), "display_order": 1, "is_popular": True},
    {"name": "Jogging", "category": "cardio", "met_value": Decimal("7.00"), "display_order": 2, "is_popular": True},
    {"name": "Running", "category": "cardio", "met_value": Decimal("9.80"), "display_order": 3, "is_popular": True},
    {"name": "Cycling", "category": "cardio", "met_value": Decimal("7.50"), "display_order": 4, "is_popular": True},
    {"name": "Swimming", "category": "cardio", "met_value": Decimal("6.00"), "display_order": 5, "is_popular": True},
    {"name": "Jump Rope", "category": "cardio", "met_value": Decimal("11.80"), "display_order": 6, "is_popular": True},
    {"name": "Elliptical", "category": "cardio", "met_value": Decimal("5.00"), "display_order": 7, "is_popular": True},
    {"name": "Rowing Machine", "category": "cardio", "met_value": Decimal("7.00"), "display_order": 8, "is_popular": True},
    {"name": "Hiking", "category": "cardio", "met_value": Decimal("6.00"), "display_order": 9, "is_popular": True},
    {"name": "Stair Climber", "category": "cardio", "met_value": Decimal("8.80"), "display_order": 10, "is_popular": True},
    {"name": "Yoga", "category": "mind_body", "met_value": Decimal("2.50"), "display_order": 11, "is_popular": True},
    {"name": "Pilates", "category": "mind_body", "met_value": Decimal("3.00"), "display_order": 12, "is_popular": True},
    {"name": "Dance Fitness", "category": "cardio", "met_value": Decimal("6.50"), "display_order": 13, "is_popular": True},
    {"name": "Bodyweight Training", "category": "strength", "met_value": Decimal("3.80"), "display_order": 14, "is_popular": True},
    {"name": "Weight Training", "category": "strength", "met_value": Decimal("6.00"), "display_order": 15, "is_popular": True},
    {"name": "HIIT", "category": "cardio", "met_value": Decimal("8.00"), "display_order": 16, "is_popular": True},
    {"name": "Boxing Workout", "category": "cardio", "met_value": Decimal("7.80"), "display_order": 17, "is_popular": False},
    {"name": "Badminton", "category": "sport", "met_value": Decimal("5.50"), "display_order": 18, "is_popular": False},
    {"name": "Tennis", "category": "sport", "met_value": Decimal("7.30"), "display_order": 19, "is_popular": False},
    {"name": "Basketball", "category": "sport", "met_value": Decimal("6.50"), "display_order": 20, "is_popular": False},
]


def seed_exercise_catalog(db: Session) -> int:
    existing_names = {
        exercise_name
        for exercise_name, in db.query(ExerciseCatalog.name).all()
    }

    created_count = 0
    for exercise in EXERCISE_SEED_DATA:
        if exercise["name"] in existing_names:
            continue

        db.add(ExerciseCatalog(**exercise))
        created_count += 1

    db.commit()
    return created_count


def main() -> None:
    db = get_session_factory()(bind=get_engine())

    try:
        created_count = seed_exercise_catalog(db)
    finally:
        db.close()

    print(f"Seeded {created_count} exercise catalog rows")


if __name__ == "__main__":
    main()