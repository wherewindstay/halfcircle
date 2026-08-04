"""Bundled example data.

Two datasets ship with the package:

``load_trade()``
    Virtual land embodied in crop trade between 154 countries — the dataset the
    original R package used.

``load_faostat()``
    Reported trade in wheat and green coffee, 2000–2024, from the FAOSTAT
    Detailed Trade Matrix. Two crops that move in opposite directions along the
    income axis, which makes them a good pair for seeing what an ordering does.
"""
from __future__ import annotations

from importlib import resources

import pandas as pd

__all__ = ["load_trade", "load_flow", "load_nodes",
           "load_faostat", "load_faostat_flow", "load_faostat_nodes"]

FAOSTAT_ITEMS = ("Wheat", "Coffee, green")
FAOSTAT_YEARS = (2000, 2005, 2010, 2015, 2020, 2024)

_ITEM_ALIASES = {"wheat": "Wheat",
                 "coffee": "Coffee, green",
                 "coffee, green": "Coffee, green"}


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


# ── FAOSTAT wheat and coffee ──────────────────────────────────────────────────

def load_faostat_flow() -> pd.DataFrame:
    """22,907 reported trade flows in wheat and green coffee, in tonnes.

    Columns: ``O`` (exporter), ``D`` (importer), ``item``, ``year``, ``volume``.

    Built from the FAOSTAT Detailed Trade Matrix, ``Import quantity`` element —
    the importer's own report, which is the more complete of the two sides.
    Aggregate areas are excluded, including the ``China`` code that sums the
    mainland, Hong Kong, Macao and Taiwan and would otherwise double-count them.
    """
    return _read("faostat_flow.csv.gz")


def load_faostat_nodes() -> pd.DataFrame:
    """242 countries with attributes you can sort them by, as of 2020.

    Columns: ``country``, ``pop_total``, ``gdpc`` (GDP per capita, US$),
    ``gdp_total``, ``area_cultivation`` (agricultural land, ha), ``income_level``.

    **The attributes are fixed at one year on purpose.** Trade spans 2000–2024,
    but if the ordering moved with it you could not tell whether a trajectory
    shifted because the flows changed or because the axis did.

    Some countries have no GDP figure in FAOSTAT — Taiwan among them. Drop them
    before sorting rather than after: ``sort_values`` puts NaN last, which reads
    as "poorest" and is not what missing means.
    """
    return _read("faostat_node.csv.gz")


def load_faostat(item: str | None = None, year: int | None = None,
                 *, min_volume: float = 0.0, top_k: int | None = None
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """FAOSTAT trade as ``(flow, nodes)``, ready to draw.

    Parameters
    ----------
    item : {"Wheat", "Coffee, green"}, optional
        One crop. ``"wheat"`` and ``"coffee"`` are accepted as shorthand.
        Leave out to keep both, in which case ``item`` stays as a column.
    year : int, optional
        One of 2000, 2005, 2010, 2015, 2020, 2024. Leave out to keep all.
    min_volume : float
        Drop flows below this many tonnes. A trade matrix has a long tail of
        tiny shipments that add ink without adding pattern.
    top_k : int, optional
        Keep only flows between the ``top_k`` largest traders, by total volume
        in and out. Below about 60 nodes the labels stay readable.

    Returns
    -------
    (flow, nodes)
        ``flow`` narrows to ``O``, ``D``, ``volume`` once a single item and year
        are selected — the three columns :func:`~halfcircle.halfcircle` reads.
        ``nodes`` is filtered to the countries left in ``flow``.

    Examples
    --------
    >>> from halfcircle import halfcircle, load_faostat
    >>> flow, node = load_faostat("wheat", 2024, min_volume=1000, top_k=50)
    >>> node = node.dropna(subset=["gdpc"]).sort_values("gdpc", ascending=False)
    >>> halfcircle(flow, node, orientation="vertical", labels=False)
    """
    flow = load_faostat_flow()
    nodes = load_faostat_nodes()

    if item is not None:
        target = _ITEM_ALIASES.get(str(item).lower(), item)
        if target not in FAOSTAT_ITEMS:
            raise ValueError(f"item must be one of {FAOSTAT_ITEMS}, got {item!r}")
        flow = flow[flow["item"] == target]
    if year is not None:
        if year not in FAOSTAT_YEARS:
            raise ValueError(f"year must be one of {FAOSTAT_YEARS}, got {year!r}")
        flow = flow[flow["year"] == year]
    if min_volume:
        flow = flow[flow["volume"] >= min_volume]

    if top_k is not None:
        totals = pd.concat([flow.groupby("O")["volume"].sum(),
                            flow.groupby("D")["volume"].sum()]).groupby(level=0).sum()
        keep = set(totals.nlargest(top_k).index)
        flow = flow[flow["O"].isin(keep) & flow["D"].isin(keep)]

    # With one item and one year the other columns are constant, so hand back
    # exactly the three columns the plotting functions read.
    if item is not None and year is not None:
        flow = flow[["O", "D", "volume"]]

    traded = set(flow["O"]) | set(flow["D"])
    nodes = nodes[nodes["country"].isin(traded)]
    return flow.reset_index(drop=True), nodes.reset_index(drop=True)
