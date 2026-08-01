"""Tests — geometry against hand-computed values, behaviour against the R original."""
import numpy as np
import pandas as pd
import pytest

import matplotlib
matplotlib.use("Agg")

from halfcircle import (arc_points, compare_orders, flow_arcs, halfcircle, inspect,
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
