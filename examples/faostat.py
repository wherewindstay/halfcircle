"""Regenerate the FAOSTAT figure in the README.

    python examples/faostat.py

Wheat and green coffee in 2024, drawn on the same income axis. Both are food
crops moving between the same set of countries; ordering the nodes by GDP per
capita is what separates them.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from halfcircle import halfcircle, load_faostat, load_faostat_nodes, mean_center

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "faostat.png")


def top_names(flow, n=8):
    """The n largest traders, as a set — halfcircle labels only these.

    A set rather than a list: each panel below is sorted the same way here, but
    a set keeps working when they are not.
    """
    import pandas as pd
    totals = pd.concat([flow.groupby("O")["volume"].sum(),
                        flow.groupby("D")["volume"].sum()]).groupby(level=0).sum()
    return set(totals.nlargest(n).index)


def main():
    # One axis for both panels, so the two crops are directly comparable.
    # Countries with no GDP figure are dropped rather than sorted last.
    nodes = load_faostat_nodes().dropna(subset=["gdpc"])
    order = nodes.sort_values("gdpc", ascending=False)

    panels = [("Wheat", *load_faostat("wheat", 2024, min_volume=1000, top_k=50)),
              ("Coffee, green", *load_faostat("coffee", 2024, min_volume=500, top_k=50))]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6))
    for ax, (name, flow, _) in zip(axes, panels):
        axis = order[order["country"].isin(set(flow["O"]) | set(flow["D"]))]
        halfcircle(flow, axis, ax=ax, orientation="vertical",
                   labels=top_names(flow), label_size=7, drop_missing=True)
        mc = mean_center(flow, axis, orientation="vertical", drop_missing=True)
        ax.plot(mc.x_weighted, mc.y_weighted, "o", color="crimson", ms=6, zorder=4)
        ax.set_title(f"{name}, 2024\nmean centre {mc.x_weighted:+.3f} on the income axis",
                     fontsize=10, pad=10)

    fig.suptitle("Nodes ordered by GDP per capita, richest at the top",
                 fontsize=11, y=0.04)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
