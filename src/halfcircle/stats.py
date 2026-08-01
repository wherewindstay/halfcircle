"""Summarising a halfcircle diagram as a single point.

Every arc has a centroid. Average those centroids — weighted by volume, or not —
and the whole diagram collapses to one point whose offset from the centre tells
you how lopsided the flow field is. Reorder the nodes and watch where the point
moves: that comparison is what the measure is for.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .layout import node_positions

__all__ = ["mean_center", "MeanCenter", "compare_orders"]

# The centroid of a semicircular area sits 4r/(3π) from the diameter.
_CENTROID = 4.0 / (3.0 * np.pi)


@dataclass(frozen=True)
class MeanCenter:
    """Weighted and unweighted mean centres of the arcs."""

    x_weighted: float
    y_weighted: float
    r_weighted: float
    x_unweighted: float
    y_unweighted: float
    r_unweighted: float
    n_arcs: int
    total_volume: float

    def as_dict(self) -> dict:
        return asdict(self)

    def __repr__(self) -> str:                              # pragma: no cover
        return (f"MeanCenter(weighted=({self.x_weighted:.3f}, {self.y_weighted:.3f}), "
                f"r={self.r_weighted:.3f}; unweighted=({self.x_unweighted:.3f}, "
                f"{self.y_unweighted:.3f}), r={self.r_unweighted:.3f}; n={self.n_arcs})")


def mean_center(flow: pd.DataFrame, nodes, *, orientation: str = "horizontal",
                drop_missing: bool = False) -> MeanCenter:
    """Mean centre of every arc in the diagram.

    A point near the origin means the flows balance out. A point pushed to one
    side means volume is running consistently in one direction.
    """
    pos = node_positions(nodes)
    o, d, v = (flow.iloc[:, i] for i in range(3))

    xs = ys = rs = 0.0
    xs_u = ys_u = rs_u = 0.0
    total = 0.0
    count = 0

    for oi, di, vi in zip(o.astype(str), d.astype(str), v):
        if oi not in pos.index or di not in pos.index:
            if drop_missing:
                continue
            raise ValueError(f"node not found in nodes: {oi if oi not in pos.index else di}")
        xo, xd = pos[oi], pos[di]
        radius = (-xo + xd) / 2.0            # sign convention of the original R package
        if radius == 0:
            continue
        w = float(vi)
        if orientation == "vertical":
            cx, cy = radius * _CENTROID, (-xo - xd) / 2.0
        else:
            cx, cy = (xo + xd) / 2.0, radius * _CENTROID
        xs += w * cx; ys += w * cy; rs += w * radius
        xs_u += cx;  ys_u += cy;  rs_u += radius
        total += w
        count += 1

    if count == 0:
        raise ValueError("no drawable flows (every row was a self-flow or missing)")
    if total == 0:
        raise ValueError("total volume is zero — cannot compute a weighted centre")

    return MeanCenter(xs / total, ys / total, rs / total,
                      xs_u / count, ys_u / count, rs_u / count,
                      count, total)


def compare_orders(flow: pd.DataFrame, orders: dict[str, object], *,
                   orientation: str = "horizontal",
                   drop_missing: bool = False) -> pd.DataFrame:
    """Mean centre under several node orderings, side by side.

    This is the inspection loop: sort the nodes by one attribute after another
    and see which ordering pulls the mean centre furthest off centre. The one
    that does is the attribute the flow is organised around.

    >>> compare_orders(flow, {"by GDP": node.sort_values("gdpc"),
    ...                       "by population": node.sort_values("pop_total")})
    """
    rows = []
    for label, nodes in orders.items():
        mc = mean_center(flow, nodes, orientation=orientation, drop_missing=drop_missing)
        rows.append({
            "order": label,
            "x_weighted": mc.x_weighted, "y_weighted": mc.y_weighted,
            "r_weighted": mc.r_weighted,
            "x_unweighted": mc.x_unweighted, "y_unweighted": mc.y_unweighted,
            "r_unweighted": mc.r_unweighted,
            "distance": float(np.hypot(mc.x_weighted, mc.y_weighted)),
            "n_arcs": mc.n_arcs,
        })
    return (pd.DataFrame(rows)
            .sort_values("distance", ascending=False)
            .reset_index(drop=True))
