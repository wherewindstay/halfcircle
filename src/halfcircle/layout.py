"""Geometry of the halfcircle diagram — pure computation, no drawing.

Nodes sit on a straight line through the centre of a unit circle. A flow from
``O`` to ``D`` is a half circle spanning the two, drawn **clockwise** from origin
to destination: the arc bulges to one side when the flow runs one way and to the
other side when it runs back. That asymmetry is the whole point — it lets a
bidirectional flow matrix be read at a glance.

Reference
---------
Xiao, N. and Chun, Y. (2009). Visualizing migration flows using kriskograms.
*Cartography and Geographic Information Science*, 36(2), 183–191.
https://doi.org/10.1559/152304009788188763
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["node_positions", "arc_points", "flow_arcs", "Arc"]


def node_positions(nodes: pd.DataFrame | pd.Series | list) -> pd.Series:
    """Map nodes onto the centre line, evenly spaced from -1 to 1.

    The *order* of ``nodes`` is what carries meaning: reordering them is how you
    interrogate the data. Returns a Series indexed by node name.
    """
    names = _names(nodes)
    n = len(names)
    if n < 2:
        raise ValueError("need at least two nodes")
    if names.duplicated().any():
        dup = names[names.duplicated()].unique()[:5]
        raise ValueError(f"duplicate node names: {list(dup)}")
    pos = 2.0 * np.arange(n) / (n - 1) - 1.0
    return pd.Series(pos, index=names, name="pos")


@dataclass(frozen=True)
class Arc:
    """One flow, ready to draw."""

    origin: str
    destination: str
    volume: float
    x: np.ndarray
    y: np.ndarray
    radius: float          # signed: > 0 when the origin sits to the right
    centre: float          # midpoint of the two nodes on the centre line


def arc_points(x_origin: float, x_dest: float, n: int = 200,
               orientation: str = "horizontal") -> tuple[np.ndarray, np.ndarray]:
    """Points along the half circle from ``x_origin`` to ``x_dest``.

    Which side the arc falls on encodes direction, so a flow and its reverse
    never overlap.
    """
    radius = (x_origin - x_dest) / 2.0
    if radius == 0:
        return np.array([]), np.array([])          # self-flows are not drawn
    theta = np.linspace(0.0, -np.pi if radius > 0 else np.pi, n)
    p = abs(radius) * np.cos(theta) + x_origin - radius
    q = abs(radius) * np.sin(theta)
    return (q, -p) if orientation == "vertical" else (p, q)


def flow_arcs(flow: pd.DataFrame, nodes, *, orientation: str = "horizontal",
              n: int = 200, drop_missing: bool = False) -> list[Arc]:
    """Turn an edge list into drawable arcs.

    ``flow`` is read positionally: origin, destination, volume — matching the
    original R package, so existing data files work unchanged.
    """
    if flow.shape[1] < 3:
        raise ValueError("flow needs at least three columns: origin, destination, volume")
    pos = node_positions(nodes)
    o, d, v = (flow.iloc[:, i] for i in range(3))

    unknown = set(pd.concat([o, d]).astype(str)) - set(pos.index)
    if unknown:
        listed = sorted(unknown)[:5]
        if not drop_missing:
            raise ValueError(
                f"{len(unknown)} node(s) appear in flow but not in nodes: {listed}"
                " — pass drop_missing=True to skip them")

    arcs: list[Arc] = []
    for oi, di, vi in zip(o.astype(str), d.astype(str), v):
        if oi not in pos.index or di not in pos.index:
            continue
        xo, xd = pos[oi], pos[di]
        if xo == xd:
            continue
        x, y = arc_points(xo, xd, n=n, orientation=orientation)
        arcs.append(Arc(oi, di, float(vi), x, y, (xo - xd) / 2.0, (xo + xd) / 2.0))
    return arcs


def _names(nodes) -> pd.Index:
    if isinstance(nodes, pd.DataFrame):
        return pd.Index(nodes.iloc[:, 0].astype(str))
    if isinstance(nodes, pd.Series):
        return pd.Index(nodes.astype(str))
    return pd.Index([str(x) for x in nodes])
