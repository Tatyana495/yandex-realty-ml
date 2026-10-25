"""Простые дополнительные признаки для CatBoost.

Не используются цена или идентификаторы квартиры/дома: утечек цели нет.
"""

import numpy as np
import pandas as pd


def prepare_catboost_features(data: pd.DataFrame) -> pd.DataFrame:
    """Преобразуем столбцы и создаём отношения площадей/этажа."""
    x = data.copy()
    x["building_type_int"] = x["building_type_int"].fillna("unknown").astype(str)

    for column in x.columns.difference(["building_type_int"]):
        x[column] = pd.to_numeric(x[column], errors="coerce")

    # Деление на ноль даёт NaN. CatBoost работает с NaN в числовых признаках.
    def safe_ratio(numerator: str, denominator: str):
        return x[numerator] / x[denominator].replace(0, np.nan)

    x["relative_floor"] = safe_ratio("floor", "floors_total")
    x["living_share"] = safe_ratio("living_area", "total_area")
    x["kitchen_share"] = safe_ratio("kitchen_area", "total_area")
    x["area_per_room"] = x["total_area"] / x["rooms"].replace(0, np.nan)
    x = x.replace([np.inf, -np.inf], np.nan)
    return x
