"""Ridge и CatBoost: обучение с честной групповой валидацией."""

from pathlib import Path

import joblib
import pandas as pd
import yaml
from catboost import CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ml.features import prepare_catboost_features


ROOT = Path(__file__).resolve().parents[2]
TARGET = "price"
IGNORE = {"price", "flat_id", "building_id"}
CATEGORICAL = ["building_type_int"]


def main():
    with (ROOT / "params.yaml").open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    alpha = float(config["train"]["alpha"])
    cb_config = config["train"]["catboost"]
    iterations = int(cb_config["iterations"])
    depth = int(cb_config["depth"])
    learning_rate = float(cb_config["learning_rate"])
    l2_leaf_reg = float(cb_config["l2_leaf_reg"])
    random_seed = int(cb_config["random_seed"])
    validation_size = float(cb_config["validation_size"])
    early_stopping_rounds = int(cb_config["early_stopping_rounds"])

    data = pd.read_csv(ROOT / "data" / "ml" / "train.csv")
    features = [col for col in data.columns if col not in IGNORE]
    if not all(col in features for col in CATEGORICAL):
        raise ValueError("Нет столбца building_type_int")
    required = {"floor", "floors_total", "living_area", "kitchen_area", "total_area", "rooms"}
    if not required.issubset(features):
        raise ValueError(f"Нет признаков для CatBoost: {sorted(required - set(features))}")

    x = data[features].copy()
    y = pd.to_numeric(data[TARGET], errors="raise")
    numeric = [col for col in features if col not in CATEGORICAL]
    x[numeric] = x[numeric].apply(pd.to_numeric, errors="coerce")
    x[CATEGORICAL] = x[CATEGORICAL].fillna("unknown").astype(str)

    # Оставляем исходную Ridge без изменений, чтобы метрики были сопоставимы.
    ridge = Pipeline([
        ("preprocess", ColumnTransformer([
            ("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]), numeric),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ])),
        ("regression", Ridge(alpha=alpha)),
    ])
    ridge.fit(x, y)

    baseline = DummyRegressor(strategy="median")
    baseline.fit(x, y)

    # Внутренняя валидация ТОЛЬКО на train, по домам.
    # Тестовая выборка нигде в обучении/подборе числа деревьев не участвует.
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=validation_size, random_state=random_seed
    )
    subtrain_idx, validation_idx = next(
        splitter.split(data, groups=data["building_id"])
    )
    assert set(data.iloc[subtrain_idx]["building_id"]).isdisjoint(
        set(data.iloc[validation_idx]["building_id"])
    )

    x_boost = prepare_catboost_features(x)
    common = dict(
        depth=depth,
        learning_rate=learning_rate,
        l2_leaf_reg=l2_leaf_reg,
        loss_function="MAE",
        eval_metric="MAE",
        random_seed=random_seed,
        thread_count=4,
        allow_writing_files=False,
        verbose=200,
    )

    print("Подбираем число деревьев CatBoost на валидации по домам...")
    selection_model = CatBoostRegressor(iterations=iterations, **common)
    selection_model.fit(
        x_boost.iloc[subtrain_idx], y.iloc[subtrain_idx],
        cat_features=CATEGORICAL,
        eval_set=(x_boost.iloc[validation_idx], y.iloc[validation_idx]),
        early_stopping_rounds=early_stopping_rounds,
        use_best_model=True,
    )
    best_iteration = selection_model.get_best_iteration()
    best_trees = iterations if best_iteration is None else max(1, int(best_iteration) + 1)

    # После выбора числа деревьев обучаем финальную модель на ВСЕЙ train-выборке.
    print(f"Обучаем финальный CatBoost: {best_trees} деревьев, {len(data)} квартир")
    catboost = CatBoostRegressor(iterations=best_trees, **common)
    catboost.fit(x_boost, y, cat_features=CATEGORICAL)

    output = ROOT / "models" / "price_model.joblib"
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": ridge,
        "baseline": baseline,
        "catboost": catboost,
        "features": features,
        "catboost_features": list(x_boost.columns),
        "catboost_trees": best_trees,
    }, output)
    print(f"Ridge и CatBoost сохранены: {output}")


if __name__ == "__main__":
    main()
