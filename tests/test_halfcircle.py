"""Tests — geometry against hand-computed values, behaviour against the R original."""
import numpy as np
import pandas as pd
import pytest

import matplotlib
matplotlib.use("Agg")

from halfcircle import (arc_points, compare_orders, flow_arcs, halfcircle, inspect,
                        load_faostat, load_faostat_flow, load_faostat_nodes,
                        load_trade, mean_center, node_positions, plot_mean_center)


@pytest.fixture
def toy():
    nodes = pd.DataFrame({"name": list("ABCD")})
    flow = pd.DataFrame({"O": ["A", "C", "B", "A"],
                         "D": ["C", "A", "D", "A"],      # last row is a self-flow
                         "v": [10.0, 5.0, 2.0, 99.0]})
    return flow, nodes


def test_nodes_span_minus_one_to_one():
    pos = node_positions(pd.DataFrame({"n": list("ABCDE")}))
    assert pos.iloc[0] == pytest.approx(-1.0)
    assert pos.iloc[-1] == pytest.approx(1.0)
    assert np.allclose(np.diff(pos.to_numpy()), 0.5)       # evenly spaced


def test_two_nodes_is_the_minimum():
    with pytest.raises(ValueError):
        node_positions(pd.DataFrame({"n": ["only"]}))


def test_duplicate_nodes_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        node_positions(pd.DataFrame({"n": ["A", "B", "A"]}))


def test_arc_is_a_half_circle_on_the_midpoint():
    x, y = arc_points(1.0, -1.0)                            # radius 1, centre 0
    assert np.hypot(x, y).max() == pytest.approx(1.0, abs=1e-9)
    assert x[0] == pytest.approx(1.0)                       # starts at the origin node
    assert x[-1] == pytest.approx(-1.0)                     # ends at the destination
    assert y.max() <= 1e-9                                  # bulges below when O is right


def test_direction_flips_the_arc():
    _, down = arc_points(1.0, -1.0)
    _, up = arc_points(-1.0, 1.0)
    assert down.min() < 0 < up.max()                        # a flow and its reverse never overlap


def test_self_flow_is_not_drawn(toy):
    flow, nodes = toy
    arcs = flow_arcs(flow, nodes)
    assert len(arcs) == 3                                   # the A→A row is dropped
    assert all(a.origin != a.destination for a in arcs)


def test_unknown_node_is_an_error_unless_asked_to_drop():
    nodes = pd.DataFrame({"n": ["A", "B"]})
    flow = pd.DataFrame({"O": ["A"], "D": ["Z"], "v": [1.0]})
    with pytest.raises(ValueError, match="not in nodes"):
        flow_arcs(flow, nodes)
    assert flow_arcs(flow, nodes, drop_missing=True) == []


def test_vertical_is_the_horizontal_rotated():
    xh, yh = arc_points(1.0, -1.0, orientation="horizontal")
    xv, yv = arc_points(1.0, -1.0, orientation="vertical")
    assert np.allclose(xv, yh)
    assert np.allclose(yv, -xh)


def test_symmetric_flows_centre_on_the_origin():
    """Equal volume both ways should cancel out."""
    nodes = pd.DataFrame({"n": ["A", "B"]})
    flow = pd.DataFrame({"O": ["A", "B"], "D": ["B", "A"], "v": [7.0, 7.0]})
    mc = mean_center(flow, nodes)
    assert mc.x_weighted == pytest.approx(0.0, abs=1e-12)
    assert mc.y_weighted == pytest.approx(0.0, abs=1e-12)


def test_one_way_flow_pushes_the_centre_off_origin():
    nodes = pd.DataFrame({"n": ["A", "B"]})
    flow = pd.DataFrame({"O": ["A"], "D": ["B"], "v": [7.0]})
    mc = mean_center(flow, nodes)
    assert mc.y_weighted == pytest.approx(4.0 / (3 * np.pi), abs=1e-12)
    assert mc.n_arcs == 1


def test_weighting_moves_the_centre(toy):
    flow, nodes = toy
    mc = mean_center(flow, nodes)
    assert (mc.x_weighted, mc.y_weighted) != (mc.x_unweighted, mc.y_unweighted)
    assert mc.total_volume == pytest.approx(17.0)           # the self-flow's 99 is excluded


def test_compare_orders_ranks_by_distance(toy):
    flow, nodes = toy
    out = compare_orders(flow, {"forward": nodes,
                                "reversed": nodes.iloc[::-1]})
    assert list(out["order"]) and out["distance"].is_monotonic_decreasing
    assert len(out) == 2


def test_example_data_loads_and_matches_the_r_package():
    flow, node = load_trade()
    assert flow.shape == (10866, 6)
    assert node.shape == (154, 8)
    assert list(flow.columns[:3]) == ["O", "D", "vegetable"]
    assert node.columns[0] == "country"


# ── the FAOSTAT dataset ───────────────────────────────────────────────────────

def test_faostat_data_loads():
    flow, node = load_faostat_flow(), load_faostat_nodes()
    assert flow.shape == (22907, 5)
    assert list(flow.columns) == ["O", "D", "item", "year", "volume"]
    assert node.shape == (242, 6)
    assert node.columns[0] == "country"
    assert sorted(flow["item"].unique()) == ["Coffee, green", "Wheat"]
    assert sorted(flow["year"].unique()) == [2000, 2005, 2010, 2015, 2020, 2024]


def test_faostat_excludes_the_aggregate_china_code():
    """FAOSTAT code 351 sums the mainland, Hong Kong, Macao and Taiwan.

    Left in alongside the parts it reports, one country would be counted twice.
    """
    names = set(load_faostat_nodes()["country"])
    assert "China" not in names
    assert "China, mainland" in names


def test_faostat_selection_narrows_to_the_three_plotting_columns():
    flow, node = load_faostat("wheat", 2024)
    assert list(flow.columns) == ["O", "D", "volume"]
    assert set(node["country"]) == set(flow["O"]) | set(flow["D"])

    both, _ = load_faostat()                      # unfiltered keeps item/year
    assert "item" in both.columns and "year" in both.columns


def test_faostat_filters_do_what_they_say():
    flow, _ = load_faostat("coffee", 2020, min_volume=500)
    assert flow["volume"].min() >= 500

    small, node = load_faostat("wheat", 2024, top_k=20)
    assert len(set(small["O"]) | set(small["D"])) <= 20
    assert len(node) <= 20


@pytest.mark.parametrize("kwargs", [{"item": "rice", "year": 2024},
                                    {"item": "wheat", "year": 2021}])
def test_faostat_rejects_what_it_does_not_have(kwargs):
    with pytest.raises(ValueError, match="must be one of"):
        load_faostat(**kwargs)


def test_faostat_wheat_and_coffee_lean_opposite_ways_on_income():
    """The reason both crops ship: they are a contrast, not two of the same.

    Coffee runs from poorer growers to richer buyers, so its mean centre sits on
    the opposite side of the income axis from wheat's.
    """
    node = load_faostat_nodes().dropna(subset=["gdpc"])
    order = node.sort_values("gdpc", ascending=False)
    wheat, _ = load_faostat("wheat", 2024, min_volume=1000)
    coffee, _ = load_faostat("coffee", 2024, min_volume=500)

    x_wheat = mean_center(wheat, order, orientation="vertical",
                          drop_missing=True).x_weighted
    x_coffee = mean_center(coffee, order, orientation="vertical",
                           drop_missing=True).x_weighted
    assert x_coffee < 0 < x_wheat


def test_plotting_runs_end_to_end():
    flow, node = load_trade()
    sub = flow.loc[flow["vegetable"] > 5000, ["O", "D", "vegetable"]]
    node = node.sort_values("gdpc", ascending=False)
    ax = halfcircle(sub, node, orientation="vertical", labels=False, drop_missing=True)
    assert ax.get_xlim() == (-1.15, 1.15)

    ax2, mc = plot_mean_center(sub, node, drop_missing=True)
    assert mc.n_arcs > 0

    fig, axes = inspect(sub, {"gdp": node, "reverse": node.iloc[::-1]},
                        labels=False, drop_missing=True)
    assert len(axes) == 2


def test_per_arc_styling_length_is_checked(toy):
    flow, nodes = toy
    with pytest.raises(ValueError, match="flow_color"):
        halfcircle(flow, nodes, flow_color=["red", "blue"])   # 3 arcs, 2 colors


def test_arcs_remember_which_flow_row_they_came_from():
    nodes = pd.DataFrame({"n": ["A", "B", "C"]})
    flow = pd.DataFrame({"O": ["A", "Z", "B"],
                         "D": ["B", "A", "C"],
                         "v": [1.0, 9.0, 2.0]})
    arcs = flow_arcs(flow, nodes, drop_missing=True)
    assert [a.row for a in arcs] == [0, 2]                    # the Z row is gone


def test_per_arc_styling_may_be_given_per_flow_row():
    """The natural thing to write is one colour per row of the flow table.

    Rows get skipped, so that list is longer than the arcs — it must be selected
    down, not zipped blindly, or every colour after the first gap is wrong.
    """
    nodes = pd.DataFrame({"n": ["A", "B", "C"]})
    flow = pd.DataFrame({"O": ["A", "Z", "B"],
                         "D": ["B", "A", "C"],
                         "v": [1.0, 9.0, 2.0]})
    ax = halfcircle(flow, nodes, flow_color=["red", "green", "blue"],
                    drop_missing=True)
    assert [line.get_color() for line in ax.lines] == ["red", "blue"]


def test_labels_can_be_a_set_of_names():
    nodes = pd.DataFrame({"n": ["A", "B", "C"]})
    flow = pd.DataFrame({"O": ["A"], "D": ["C"], "v": [1.0]})
    ax = halfcircle(flow, nodes, labels={"B"})
    assert [t.get_text() for t in ax.texts] == ["B"]


def test_a_label_set_survives_reordering():
    """`inspect` sorts each panel differently, so positional labels would drift."""
    nodes = pd.DataFrame({"n": ["A", "B", "C"]})
    flow = pd.DataFrame({"O": ["A"], "D": ["C"], "v": [1.0]})
    _, axes = inspect(flow, {"fwd": nodes, "rev": nodes.iloc[::-1]}, labels={"A"})
    for ax in axes:
        assert [t.get_text() for t in ax.texts] == ["A"]


def test_four_panels_are_laid_out_two_by_two():
    nodes = pd.DataFrame({"n": ["A", "B", "C"]})
    flow = pd.DataFrame({"O": ["A"], "D": ["C"], "v": [1.0]})
    fig, axes = inspect(flow, {k: nodes for k in "abcd"})
    assert len(axes) == 4
    assert len(fig.axes) == 4                    # 2x2, not 3+1 with two blanks


# ── significance testing ──────────────────────────────────────────────────

def test_random_ordering_is_not_significant():
    """A meaningless ordering should not beat chance — that is the control."""
    from halfcircle import order_significance
    import numpy as np

    rng = np.random.default_rng(0)
    names = [f"n{i}" for i in range(12)]
    flow = pd.DataFrame({"O": rng.choice(names, 60), "D": rng.choice(names, 60),
                         "v": rng.random(60)})
    res = order_significance(flow, names, n_permutations=199, random_state=0)
    assert 0 < res.p_value <= 1
    assert res.p_value > 0.05          # random data, arbitrary order → no signal


def test_engineered_ordering_is_significant():
    """Long flows all running the same way up the ordering are a real signal.

    Note the arcs have to *span* the ordering: a chain of neighbour-to-neighbour
    flows draws tiny half circles whose centroids sit near the origin no matter
    which way they point, so distance alone would not detect it.
    """
    from halfcircle import order_significance

    names = [f"n{i}" for i in range(12)]
    rows = [(names[i], names[i + 6], 1.0) for i in range(6)]    # first half → second half
    flow = pd.DataFrame(rows, columns=["O", "D", "v"])
    res = order_significance(flow, names, n_permutations=199, random_state=0)
    assert res.p_value < 0.05
    assert res.distance > res.null_mean


def test_p_value_never_reaches_zero():
    from halfcircle import order_significance
    names = list("ABCDE")
    flow = pd.DataFrame({"O": ["A", "B", "C"], "D": ["B", "C", "D"], "v": [1.0, 1.0, 1.0]})
    res = order_significance(flow, names, n_permutations=99, random_state=1)
    assert res.p_value >= 1 / (99 + 1)


def test_identical_flows_are_not_distinguishable():
    from halfcircle import compare_flows
    names = list("ABCDE")
    f = pd.DataFrame({"O": ["A", "B", "C", "D"], "D": ["B", "C", "D", "E"],
                      "v": [1.0, 2.0, 3.0, 4.0]})
    res = compare_flows(f, f.copy(), names, n_permutations=199, random_state=0)
    assert res.separation == pytest.approx(0.0, abs=1e-12)
    assert res.p_value > 0.05


def test_opposite_flows_are_distinguishable():
    from halfcircle import compare_flows
    names = [f"n{i}" for i in range(10)]
    fwd = pd.DataFrame([(names[i], names[i + 5], 1.0) for i in range(5)],
                       columns=["O", "D", "v"])
    rev = pd.DataFrame([(names[i + 5], names[i], 1.0) for i in range(5)],
                       columns=["O", "D", "v"])
    res = compare_flows(fwd, rev, names, n_permutations=199, random_state=0,
                        label_a="forward", label_b="reverse")
    assert res.separation > 0.1        # mirrored arcs land on opposite sides
    assert res.p_value < 0.05


# ── time series ───────────────────────────────────────────────────────────

def test_track_reports_movement_between_periods():
    from halfcircle import track
    names = list("ABCDE")
    p1 = pd.DataFrame({"O": ["A"], "D": ["E"], "v": [1.0]})
    p2 = pd.DataFrame({"O": ["E"], "D": ["A"], "v": [1.0]})
    df = track({"t1": p1, "t2": p2}, names)
    assert list(df["period"]) == ["t1", "t2"]
    assert np.isnan(df.loc[0, "step"])              # nothing to compare the first to
    assert df.loc[1, "step"] > 0                    # the reversal moved the centre


def test_track_splits_skew_and_spread_axes():
    from halfcircle import track
    names = list("ABCDE")
    f = pd.DataFrame({"O": ["A"], "D": ["E"], "v": [1.0]})
    h = track({"p": f}, names, orientation="horizontal")
    v = track({"p": f}, names, orientation="vertical")
    assert h.loc[0, "skew_axis"] == h.loc[0, "y"]   # horizontal: direction reads on y
    assert v.loc[0, "skew_axis"] == v.loc[0, "x"]   # vertical: direction reads on x


def test_plot_track_runs():
    from halfcircle import plot_track
    names = list("ABCDE")
    periods = {"t1": pd.DataFrame({"O": ["A"], "D": ["E"], "v": [1.0]}),
               "t2": pd.DataFrame({"O": ["B"], "D": ["D"], "v": [2.0]})}
    ax, df = plot_track(periods, names)
    assert len(df) == 2
