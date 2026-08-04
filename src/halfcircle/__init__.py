"""halfcircle — read bidirectional flow data at a glance.

Nodes sit on a line through the centre of a circle; each flow is a half circle
drawn clockwise from origin to destination. Reorder the nodes and the pattern
either scatters or snaps into place — that comparison is the analysis.

    from halfcircle import halfcircle, load_trade, compare_orders

    flow, node = load_trade()
    flow = flow.loc[flow["vegetable"] > 5000, ["O", "D", "vegetable"]]
    halfcircle(flow, node.sort_values("gdpc", ascending=False), orientation="vertical")

A Python rewrite of the R package of the same name
(Park & Xiao, CRAN 2018), extended for interactive inspection.
"""
from .layout import Arc, arc_points, flow_arcs, node_positions
from .stats import MeanCenter, compare_orders, mean_center
from .plot import halfcircle, inspect, plot_mean_center
from .testing import FlowComparison, OrderTest, compare_flows, order_significance
from .series import plot_track, track
from .datasets import (load_faostat, load_faostat_flow, load_faostat_nodes,
                       load_flow, load_nodes, load_trade)

__version__ = "0.4.0"
__all__ = [
    "halfcircle", "inspect", "plot_mean_center",
    "mean_center", "compare_orders", "MeanCenter",
    "order_significance", "compare_flows", "OrderTest", "FlowComparison",
    "track", "plot_track",
    "node_positions", "arc_points", "flow_arcs", "Arc",
    "load_trade", "load_flow", "load_nodes",
    "load_faostat", "load_faostat_flow", "load_faostat_nodes",
]
