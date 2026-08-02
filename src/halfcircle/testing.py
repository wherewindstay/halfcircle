"""Is the pattern real, or would any ordering look like this?

A halfcircle diagram always *looks* like something. The question is whether the
ordering you chose explains the flow better than an arbitrary one would. These
functions answer that by shuffling: reorder the nodes at random many times, build
the null distribution of mean-centre offsets, and see where the real ordering falls.

The same machinery answers a second question — whether two flow variables
(cereals and vegetables, say, or the same commodity in two decades) are organised
differently, by shuffling which rows belong to which variable.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .stats import mean_center

__all__ = ["order_significance", "compare_flows", "OrderTest", "FlowComparison"]


@dataclass(frozen=True)
class OrderTest:
    """How unusual the observed ordering is against random orderings."""

    distance: float             # observed offset of the mean centre from the origin
    x: float
    y: float
    p_value: float              # P(random offset >= observed)
    p_x: float                  # one-sided on the x component alone
    p_y: float                  # one-sided on the y component alone
    null_mean: float
    null_sd: float
    z_score: float
    n_permutations: int

    def __repr__(self) -> str:                                  # pragma: no cover
        return (f"OrderTest(distance={self.distance:.3f}, p={self.p_value:.4f}, "
                f"z={self.z_score:.2f}, null={self.null_mean:.3f}±{self.null_sd:.3f})")

    def summary(self) -> str:
        verdict = ("stronger than chance" if self.p_value < 0.05
                   else "not distinguishable from chance")
        return (f"mean centre {self.distance:.3f} from origin "
                f"(random orderings: {self.null_mean:.3f} ± {self.null_sd:.3f}) — "
                f"p = {self.p_value:.4f}, {verdict}")


def order_significance(flow: pd.DataFrame, nodes, *, n_permutations: int = 999,
                       orientation: str = "horizontal", random_state=None,
                       drop_missing: bool = False) -> OrderTest:
    """Test one ordering against randomly shuffled orderings.

    The null hypothesis is that node order carries no information: if that were
    true, shuffling the nodes would give mean-centre offsets as large as the one
    you observed. A small p-value means the attribute you sorted by really does
    organise the flow.

    ``p_x`` and ``p_y`` test the two components separately, which matters because
    they mean different things. With ``orientation="vertical"``, the horizontal
    component measures **directional imbalance** — how consistently volume runs
    one way along the ordering — while the vertical component measures **where
    along the ordering** the flows concentrate.

    >>> res = order_significance(flow, node.sort_values("income_level"))
    >>> print(res.summary())
    mean centre 0.722 from origin (random orderings: 0.104 ± 0.061) — p = 0.0010, stronger than chance
    """
    rng = np.random.default_rng(random_state)
    names = _names(nodes)

    obs = mean_center(flow, names, orientation=orientation, drop_missing=drop_missing)
    d_obs = float(np.hypot(obs.x_weighted, obs.y_weighted))

    dists = np.empty(n_permutations)
    xs = np.empty(n_permutations)
    ys = np.empty(n_permutations)
    order = np.arange(len(names))
    for i in range(n_permutations):
        rng.shuffle(order)
        mc = mean_center(flow, names[order], orientation=orientation,
                         drop_missing=drop_missing)
        xs[i], ys[i] = mc.x_weighted, mc.y_weighted
        dists[i] = np.hypot(mc.x_weighted, mc.y_weighted)

    # +1 in numerator and denominator: the observed arrangement is itself one of
    # the possible arrangements, which keeps the test from ever reporting p = 0.
    p = (np.sum(dists >= d_obs) + 1) / (n_permutations + 1)
    p_x = (np.sum(np.abs(xs) >= abs(obs.x_weighted)) + 1) / (n_permutations + 1)
    p_y = (np.sum(np.abs(ys) >= abs(obs.y_weighted)) + 1) / (n_permutations + 1)
    sd = float(dists.std(ddof=1))

    return OrderTest(d_obs, obs.x_weighted, obs.y_weighted,
                     float(p), float(p_x), float(p_y),
                     float(dists.mean()), sd,
                     float((d_obs - dists.mean()) / sd) if sd > 0 else float("nan"),
                     n_permutations)


@dataclass(frozen=True)
class FlowComparison:
    """Whether two flow variables sit differently under the same ordering."""

    label_a: str
    label_b: str
    distance_a: float
    distance_b: float
    separation: float           # distance between the two mean centres
    p_value: float
    n_permutations: int

    def __repr__(self) -> str:                                  # pragma: no cover
        return (f"FlowComparison({self.label_a}={self.distance_a:.3f} vs "
                f"{self.label_b}={self.distance_b:.3f}, sep={self.separation:.3f}, "
                f"p={self.p_value:.4f})")

    def summary(self) -> str:
        verdict = "differ" if self.p_value < 0.05 else "are not distinguishable"
        return (f"{self.label_a} ({self.distance_a:.3f}) and {self.label_b} "
                f"({self.distance_b:.3f}) {verdict}: centres {self.separation:.3f} "
                f"apart, p = {self.p_value:.4f}")


def compare_flows(flow_a: pd.DataFrame, flow_b: pd.DataFrame, nodes, *,
                  label_a: str = "A", label_b: str = "B",
                  n_permutations: int = 999, orientation: str = "horizontal",
                  random_state=None, drop_missing: bool = False) -> FlowComparison:
    """Test whether two flow variables are organised differently.

    Cereals against vegetables; the same commodity in 1990 against 2020. Both
    are the same question: do these two flow fields sit in different places under
    the same node ordering, by more than sampling noise would give?

    The test pools every edge from both tables, reassigns them to two groups at
    random keeping the group sizes, and asks how often the two mean centres end
    up as far apart as they actually are.

    >>> compare_flows(cereals, vegetables, node.sort_values("income_level"),
    ...               label_a="cereals", label_b="vegetables")
    """
    a = flow_a.iloc[:, :3].copy(); a.columns = ["O", "D", "v"]
    b = flow_b.iloc[:, :3].copy(); b.columns = ["O", "D", "v"]
    names = _names(nodes)

    mc_a = mean_center(a, names, orientation=orientation, drop_missing=drop_missing)
    mc_b = mean_center(b, names, orientation=orientation, drop_missing=drop_missing)
    obs_sep = float(np.hypot(mc_a.x_weighted - mc_b.x_weighted,
                             mc_a.y_weighted - mc_b.y_weighted))

    pooled = pd.concat([a, b], ignore_index=True)
    n_a = len(a)
    rng = np.random.default_rng(random_state)
    idx = np.arange(len(pooled))

    seps = np.empty(n_permutations)
    for i in range(n_permutations):
        rng.shuffle(idx)
        pa = pooled.iloc[idx[:n_a]]
        pb = pooled.iloc[idx[n_a:]]
        ma = mean_center(pa, names, orientation=orientation, drop_missing=drop_missing)
        mb = mean_center(pb, names, orientation=orientation, drop_missing=drop_missing)
        seps[i] = np.hypot(ma.x_weighted - mb.x_weighted,
                           ma.y_weighted - mb.y_weighted)

    p = (np.sum(seps >= obs_sep) + 1) / (n_permutations + 1)
    return FlowComparison(label_a, label_b,
                          float(np.hypot(mc_a.x_weighted, mc_a.y_weighted)),
                          float(np.hypot(mc_b.x_weighted, mc_b.y_weighted)),
                          obs_sep, float(p), n_permutations)


def _names(nodes) -> pd.Index:
    if isinstance(nodes, pd.DataFrame):
        return pd.Index(nodes.iloc[:, 0].astype(str))
    if isinstance(nodes, pd.Series):
        return pd.Index(nodes.astype(str))
    return pd.Index([str(x) for x in nodes])
