"""Bundled example data — virtual land trade between countries."""
from __future__ import annotations

from importlib import resources

import pandas as pd

__all__ = ["load_trade", "load_flow", "load_nodes"]


def _read(name: str) -> pd.DataFrame:
    with resources.files(__package__).joinpath("data", name).open("rb") as fh:
        return pd.read_csv(fh, compression="gzip")


def load_flow() -> pd.DataFrame:
    """10,866 country pairs with land embodied in crop trade, in hectares.

    Columns: ``O``, ``D``, ``vegetable``, ``fruit``, ``wheat``, ``soybean``.
    """
    return _read("ex_flow.csv.gz")


def load_nodes() -> pd.DataFrame:
    """154 countries with attributes you can sort them by.

    Columns: ``country``, ``x``, ``y``, ``pop_total``, ``gdpc``,
    ``area_cultivation``, ``water_total``, ``income_level``.
    """
    return _read("ex_node.csv.gz")


def load_trade() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Both tables at once: ``(flow, nodes)``."""
    return load_flow(), load_nodes()
