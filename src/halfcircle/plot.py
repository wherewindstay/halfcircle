"""Drawing halfcircle diagrams with matplotlib."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .layout import flow_arcs, node_positions
from .stats import mean_center

__all__ = ["halfcircle", "plot_mean_center", "inspect"]

_MAX_WIDTH = 10.0


def halfcircle(flow: pd.DataFrame, nodes, *, orientation: str = "horizontal",
               ax=None, circle_color: str = "lightgray", circle_alpha: float = 0.5,
               flow_color="black", flow_alpha: float = 0.5, flow_width="proportional",
               node_color="black", node_size: float = 4.0, node_alpha: float = 0.7,
               labels=True, label_size: float = 6.0, label_color: str = "black",
               label_gap: float = 0.1, arc_points: int = 200,
               drop_missing: bool = False, title: str | None = None):
    """Draw a halfcircle diagram and return the Axes.

    Parameters
    ----------
    flow : DataFrame
        Edge list. The first three columns are read positionally as origin,
        destination and volume.
    nodes : DataFrame, Series or sequence
        Node names in the order they should appear on the centre line. **This
        order is the analysis** — sort it by whatever attribute you suspect the
        flow is organised around.
    orientation : {"horizontal", "vertical"}
        Which axis the centre line runs along.
    flow_color, flow_width
        A single value, or one value per row of ``flow`` for per-arc control.
        ``flow_width="proportional"`` scales linewidth to volume.
    labels
        ``True`` for node names, ``False``/``None`` for none, or a sequence of
        your own labels.

    Examples
    --------
    >>> from halfcircle import halfcircle, load_trade
    >>> flow, node = load_trade()
    >>> flow = flow.loc[flow["vegetable"] > 5000, ["O", "D", "vegetable"]]
    >>> node = node.sort_values("gdpc", ascending=False)
    >>> halfcircle(flow, node, orientation="vertical", labels=False)
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    ax.add_patch(Circle((0, 0), 1.0, facecolor=circle_color, edgecolor="none",
                        alpha=circle_alpha, zorder=0))

    arcs = flow_arcs(flow, nodes, orientation=orientation, n=arc_points,
                     drop_missing=drop_missing)
    volumes = np.array([a.volume for a in arcs], dtype=float)
    widths = _resolve_widths(flow_width, volumes, len(arcs))
    colors = _per_arc(flow_color, len(arcs), "flow_color")

    for arc, w, c in zip(arcs, widths, colors):
        ax.plot(arc.x, arc.y, lw=w, color=c, alpha=flow_alpha,
                solid_capstyle="round", zorder=1)

    pos = node_positions(nodes)
    if orientation == "vertical":
        nx, ny = np.zeros(len(pos)), -pos.to_numpy()
    else:
        nx, ny = pos.to_numpy(), np.zeros(len(pos))
    ax.scatter(nx, ny, s=node_size, c=_per_arc(node_color, len(pos), "node_color"),
               alpha=node_alpha, zorder=2, linewidths=0)

    texts = _resolve_labels(labels, pos)
    if texts is not None:
        for x, y, t in zip(nx, ny, texts):
            if not t:
                continue
            if orientation == "vertical":
                ax.text(x + label_gap, y, t, fontsize=label_size, color=label_color,
                        va="center", ha="left", zorder=3)
            else:
                ax.text(x, y + label_gap, t, fontsize=label_size, color=label_color,
                        va="bottom", ha="center", rotation=90, zorder=3)

    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    if title:
        ax.set_title(title, fontsize=10)
    return ax


def plot_mean_center(flow: pd.DataFrame, nodes, *, orientation: str = "horizontal",
                     ax=None, drop_missing: bool = False, annotate: bool = True):
    """Draw just the mean centres — the diagram reduced to two points.

    Returns ``(ax, MeanCenter)``.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    if ax is None:
        _, ax = plt.subplots(figsize=(4.5, 4.5))

    mc = mean_center(flow, nodes, orientation=orientation, drop_missing=drop_missing)
    ax.add_patch(Circle((0, 0), 1.0, facecolor="white", edgecolor="lightgray", zorder=0))
    ax.plot(0, 0, marker="x", color="lightgray", ms=6, zorder=1)
    ax.plot(mc.x_weighted, mc.y_weighted, "o", color="black", ms=6, zorder=2)
    ax.plot(mc.x_unweighted, mc.y_unweighted, "o", mfc="none", mec="black", ms=6, zorder=2)
    if annotate:
        ax.annotate("weighted", (mc.x_weighted, mc.y_weighted),
                    textcoords="offset points", xytext=(8, 0), fontsize=7, va="center")
        ax.annotate("unweighted", (mc.x_unweighted, mc.y_unweighted),
                    textcoords="offset points", xytext=(8, 0), fontsize=7, va="center")
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    return ax, mc


def inspect(flow: pd.DataFrame, orders: dict, *, orientation: str = "horizontal",
            ncols: int | None = None, drop_missing: bool = False, **kwargs):
    """Draw the same flows under several node orderings, side by side.

    The point of the diagram is comparison: one ordering makes the flow look
    like noise, another makes it fall into a clear pattern. Seeing them together
    is how you find which one.

    Each panel is annotated with how far its mean centre sits from the origin.

    >>> inspect(flow, {"by GDP": node.sort_values("gdpc"),
    ...                "by population": node.sort_values("pop_total"),
    ...                "alphabetical": node.sort_values("country")})
    """
    import matplotlib.pyplot as plt

    n = len(orders)
    if n == 0:
        raise ValueError("orders is empty")
    ncols = ncols or min(3, n)
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 4.4 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, (label, nodes) in zip(axes, orders.items()):
        halfcircle(flow, nodes, orientation=orientation, ax=ax,
                   drop_missing=drop_missing, **kwargs)
        mc = mean_center(flow, nodes, orientation=orientation, drop_missing=drop_missing)
        dist = float(np.hypot(mc.x_weighted, mc.y_weighted))
        ax.plot(mc.x_weighted, mc.y_weighted, "o", color="crimson", ms=5, zorder=4)
        ax.set_title(f"{label}\nmean centre {dist:.3f} from origin", fontsize=9)
    for ax in axes[n:]:
        ax.axis("off")
    fig.tight_layout()
    return fig, axes[:n]


def _resolve_widths(flow_width, volumes, n):
    if isinstance(flow_width, str):
        if flow_width != "proportional":
            raise ValueError("flow_width must be 'proportional' or numeric")
        if n == 0:
            return []
        peak = volumes.max()
        if peak <= 0:
            return np.ones(n)
        return np.maximum(_MAX_WIDTH * volumes / peak, 0.2)
    return _per_arc(flow_width, n, "flow_width")


def _per_arc(value, n, name):
    if isinstance(value, (str, int, float)) or value is None:
        return [value] * n
    seq = list(value)
    if len(seq) != n:
        raise ValueError(f"{name} has {len(seq)} values but there are {n} items")
    return seq


def _resolve_labels(labels, pos):
    if labels is None or labels is False:
        return None
    if labels is True:
        return list(pos.index)
    seq = list(labels)
    if len(seq) != len(pos):
        raise ValueError(f"labels has {len(seq)} values but there are {len(pos)} nodes")
    return seq
