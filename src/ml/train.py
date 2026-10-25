"""Обучение базовой Ridge-модели и простого DummyRegressor."""

from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
TARGET = "price"
IGNORE = {"price", "flat_id", "building_id"}
CATEGORICAL = ["building_type_int"]


def main():
    with (ROOT / "params.yaml").open(encoding="utf-8") as file:
        alpha = float(yaml.safe_load(file)["train"]["alpha"])

    data = pd.read_csv(ROOT / "data" / "ml" / "train.csv")
    features = [col for col in data.columns if col not in IGNORE]
    if not all(col in features for col in CATEGORICAL):
        raise ValueError("Нет столбца building_type_int")

    X = data[features].copy()
    y = pd.to_numeric(data[TARGET], errors="raise")
    numeric = [col for col in features if col not in CATEGORICAL]
    X[numeric] = X[numeric].apply(pd.to_numeric, errors="coerce")
    X[CATEGORICAL] = X[CATEGORICAL].fillna("unknown").astype(str)

    # Все медианы, масштабирование и категории обучаются только на train.
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = OneHotEncoder(handle_unknown="ignore")
    preprocess = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric),
        ("categorical", categorical_pipeline, CATEGORICAL),
    ])
    model = Pipeline([
        ("preprocess", preprocess),
        ("regression", Ridge(alpha=alpha)),
    ])
    model.fit(X, y)

    baseline = DummyRegressor(strategy="median")
    baseline.fit(X, y)

    output = ROOT / "models" / "price_model.joblib"
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "baseline": baseline, "features": features}, output)
    print(f"Обучено на {len(data)} квартирах; alpha={alpha}")
    print(f"Модель сохранена: {output}")


if __name__ == "__main__":
    main()
