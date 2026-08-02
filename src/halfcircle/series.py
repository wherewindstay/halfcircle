"""Tracking a flow field as it changes over time.

Park, Munroe and Xiao (2023) read four decades of cereal trade by drawing one
halfcircle diagram per period and comparing them. This module makes that
comparison explicit: reduce each period to its mean centre and follow the path
those points trace.

Which way the path runs is the finding. Under ``orientation="vertical"`` the
horizontal axis carries **directional skew** — how lopsided the flow is along the
ordering — so a path drifting left means exports are running increasingly from
one end of the ordering to the other.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import mean_center

__all__ = ["track", "plot_track"]


def track(periods: dict, nodes, *, orientation: str = "horizontal",
          drop_missing: bool = False) -> pd.DataFrame:
    """Mean centre of each period, in order.

    ``periods`` maps a label to a flow table — ``{"1988-90": df1, "1998-00": df2, …}``.
    Dictionaries keep insertion order, so list them chronologically.

    Returns one row per period with the mean centre, its distance from the
    origin, and how far it moved from the previous period.

    >>> track({"1988-90": f1, "1998-00": f2, "2008-10": f3},
    ...       node.sort_values("income_level"), orientation="vertical")
    """
    rows = []
    prev = None
    for label, flow in periods.items():
        mc = mean_center(flow, nodes, orientation=orientation, drop_missing=drop_missing)
        x, y = mc.x_weighted, mc.y_weighted
        step = float(np.hypot(x - prev[0], y - prev[1])) if prev else np.nan
        rows.append({
            "period": label,
            "x": x, "y": y,
            "distance": float(np.hypot(x, y)),
            "step": step,
            "skew_axis": x if orientation == "vertical" else y,
            "spread_axis": y if orientation == "vertical" else x,
            "n_arcs": mc.n_arcs,
            "total_volume": mc.total_volume,
        })
        prev = (x, y)
    return pd.DataFrame(rows)


def plot_track(periods: dict, nodes, *, orientation: str = "horizontal",
               ax=None, drop_missing: bool = False, annotate: bool = True,
               color: str = "crimson"):
    """Draw the path the mean centre traces across periods.

    Returns ``(ax, DataFrame)`` — the picture and the numbers behind it.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    df = track(periods, nodes, orientation=orientation, drop_missing=drop_missing)
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))

    ax.add_patch(Circle((0, 0), 1.0, facecolor="white", edgecolor="lightgray", zorder=0))
    ax.plot(0, 0, marker="x", color="lightgray", ms=6, zorder=1)
    ax.plot(df["x"], df["y"], "-", color=color, lw=1.2, alpha=0.6, zorder=2)
    sizes = np.linspace(28, 70, len(df))            # later periods drawn larger
    ax.scatter(df["x"], df["y"], s=sizes, c=color, zorder=3, edgecolors="white", linewidths=0.8)

    if annotate:
        for _, r in df.iterrows():
            ax.annotate(r["period"], (r["x"], r["y"]), textcoords="offset points",
                        xytext=(9, 0), fontsize=7, va="center")

    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    return ax, df
