"""Разделение квартир по домам на обучение и тест."""

from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import GroupShuffleSplit


ROOT = Path(__file__).resolve().parents[2]


def main():
    with (ROOT / "params.yaml").open(encoding="utf-8") as file:
        params = yaml.safe_load(file)["split"]

    data = pd.read_csv(ROOT / "data" / "ml" / "clean.csv")
    if data["building_id"].isna().any():
        raise ValueError("building_id содержит пропуски: нельзя группировать дома")
    if data["building_id"].nunique() < 2:
        raise ValueError("Для разделения нужно как минимум два разных дома")
    if data["price"].isna().any():
        raise ValueError("Целевая переменная price содержит пропуски")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=float(params["test_size"]),
        random_state=int(params["random_state"]),
    )
    train_idx, test_idx = next(
        splitter.split(data, groups=data["building_id"])
    )
    train = data.iloc[train_idx].sort_values("flat_id")
    test = data.iloc[test_idx].sort_values("flat_id")

    assert set(train["building_id"]).isdisjoint(set(test["building_id"]))

    folder = ROOT / "data" / "ml"
    train.to_csv(folder / "train.csv", index=False, encoding="utf-8", lineterminator="\n")
    test.to_csv(folder / "test.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"Обучение: {len(train)}; тест: {len(test)}")
    print(f"Домов в обучении: {train['building_id'].nunique()}; в тесте: {test['building_id'].nunique()}")


if __name__ == "__main__":
    main()
