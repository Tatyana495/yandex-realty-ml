import numpy as np
import pandas as pd


def remove_duplicates(df):
    df = df.copy()

    columns = df.columns.drop("flat_id").tolist()

    df = df.sort_values("flat_id")

    df = df.drop_duplicates(
        subset=columns,
        keep="first"
    )

    return df.reset_index(drop=True)


def remove_invalid_areas(df):
    df = df.copy()

    area_sum = df["living_area"] + df["kitchen_area"]

    invalid_areas = (
        (df["living_area"] > df["total_area"])
        | (df["kitchen_area"] > df["total_area"])
        | (area_sum > df["total_area"] + 0.01)
    )

    impossible_imputation = (
        (df["living_area"] == 0)
        & (df["kitchen_area"] >= df["total_area"])
    )

    invalid_mask = invalid_areas | impossible_imputation

    print("Invalid areas:", invalid_mask.sum())

    return df.loc[~invalid_mask].reset_index(drop=True)


def clean_missing_values(df):
    df = df.copy()

    columns = ["kitchen_area", "living_area"]

    for column in columns:
        df[f"{column}_missing"] = (df[column] == 0)

        df[column] = df[column].replace(0, np.nan)

        median_by_rooms = (
            df.groupby("rooms")[column].transform("median")
        )

        df[column] = df[column].fillna(median_by_rooms)

        df[column] = df[column].fillna(df[column].median())

    area_sum = df["kitchen_area"] + df["living_area"]
    invalid = area_sum > df["total_area"]

    kitchen_missing = df["kitchen_area_missing"]
    living_missing = df["living_area_missing"]

    mask = invalid & kitchen_missing & ~living_missing

    df.loc[mask, "kitchen_area"] = (
        df.loc[mask, "total_area"]
        - df.loc[mask, "living_area"]
    ) * 0.95

    mask = invalid & living_missing & ~kitchen_missing

    df.loc[mask, "living_area"] = (
        df.loc[mask, "total_area"]
        - df.loc[mask, "kitchen_area"]
    ) * 0.95

    mask = invalid & kitchen_missing & living_missing

    scale = (
        df.loc[mask, "total_area"] * 0.95
        / area_sum.loc[mask]
    )

    df.loc[mask, "kitchen_area"] *= scale
    df.loc[mask, "living_area"] *= scale

    return df


def remove_outliers(df):
    df = df.copy()

    price_per_sqm = df["price"] / df["total_area"]

    lower_bound = 20_000
    upper_bound = 5_000_000

    outlier_mask = (
        (price_per_sqm < lower_bound)
        | (price_per_sqm > upper_bound)
    )

    print("Price outliers:", outlier_mask.sum())

    df = df.loc[~outlier_mask].copy()

    return df.reset_index(drop=True)


def clean_data(df):
    df = remove_duplicates(df)
    df = remove_invalid_areas(df)
    df = clean_missing_values(df)
    df = remove_outliers(df)

    return df
