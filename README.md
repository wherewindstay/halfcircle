**English** | [한국어](README.ko.md)

# halfcircle

Read bidirectional flow data at a glance.

![Two halfcircle diagrams of the same trade flows, ordered by GDP per capita and by population](preview.png)

Nodes sit on a line through the centre of a circle. Each flow is drawn as a half circle running clockwise from origin to destination — so a flow and its reverse bulge to opposite sides and never overlap. Reorder the nodes and the picture either scatters into noise or snaps into a pattern. **That comparison is the analysis.**

This is a Python rewrite of the [R package of the same name](https://cran.r-project.org/src/contrib/Archive/halfcircle/) (Park & Xiao, CRAN 2018), extended with tools for comparing orderings systematically.

## Install

```bash
pip install git+https://github.com/wherewindstay/halfcircle.git
```

## Quick start

```python
from halfcircle import halfcircle, load_trade

flow, node = load_trade()                    # land embodied in crop trade, 154 countries
flow = flow.loc[flow["vegetable"] > 5000, ["O", "D", "vegetable"]]
node = node.sort_values("gdpc", ascending=False)

halfcircle(flow, node, orientation="vertical", labels=False, drop_missing=True)
```

`flow` is read positionally — origin, destination, volume — so files written for the R package work unchanged.

## Finding the ordering that matters

The diagram only says something once you compare orderings. `compare_orders` does that arithmetically: it reports how far the mean centre of all arcs sits from the origin under each ordering. A centre near zero means the flows cancel out; a centre pushed far to one side means volume runs consistently in one direction.

```python
from halfcircle import compare_orders

compare_orders(flow, {
    "GDP per capita":  node.sort_values("gdpc", ascending=False),
    "Population":      node.sort_values("pop_total", ascending=False),
    "Cultivated area": node.sort_values("area_cultivation", ascending=False),
    "Alphabetical":    node.sort_values("country"),
}, drop_missing=True)
```

```
          order  x_weighted  y_weighted  distance
     Population   -0.722115    0.006337  0.722143
Cultivated area   -0.632828    0.028257  0.633458
 GDP per capita   -0.415186   -0.077493  0.422356
   Alphabetical    0.080736    0.061077  0.101236
```

Ordering countries by population pulls the mean centre furthest off origin (0.72), while alphabetical ordering leaves it near the middle (0.10) — as a meaningless ordering should. Population, not wealth, is what this particular flow is organised around.

To see it rather than read it:

```python
from halfcircle import inspect

inspect(flow, {"GDP per capita": node.sort_values("gdpc", ascending=False),
               "Population":     node.sort_values("pop_total", ascending=False)},
        orientation="vertical", labels=False, drop_missing=True)
```

Each panel is annotated with its mean-centre distance and marks the centre in red.

## API

| Function | What it does |
|---|---|
| `halfcircle(flow, nodes, ...)` | Draw the diagram, return a matplotlib `Axes` |
| `inspect(flow, orders, ...)` | Draw the same flows under several orderings, side by side |
| `mean_center(flow, nodes, ...)` | Weighted and unweighted mean centre of every arc |
| `compare_orders(flow, orders, ...)` | Mean centres for several orderings, ranked by distance |
| `plot_mean_center(flow, nodes, ...)` | The diagram reduced to its two mean-centre points |
| `node_positions`, `arc_points`, `flow_arcs` | Geometry only, if you want to draw it yourself |
| `load_trade()`, `load_flow()`, `load_nodes()` | The bundled example data |

Styling follows the R package: `flow_color`, `flow_width`, `node_color` and `labels` each take a single value or one value per row, so you can colour arcs by attribute or highlight a single node.

```python
# highlight flows touching one country
colors = ["crimson" if "China" in (o, d) else "lightgray"
          for o, d in zip(flow["O"], flow["D"])]
halfcircle(flow, node, flow_color=colors, orientation="vertical", labels=False)
```

## Notes

- Self-flows (origin equal to destination) are not drawn, and are excluded from the mean centre.
- Nodes appearing in `flow` but missing from `nodes` raise an error; pass `drop_missing=True` to skip them instead.
- `flow_width="proportional"` scales linewidth to volume, capped at 10 points, matching the R original.

## Example data

`load_trade()` returns land embodied in crop trade between 154 countries (10,866 pairs; vegetable, fruit, wheat and soybean, in hectares) together with country attributes — coordinates, population, GDP per capita, cultivated area, water use and income level — to sort by. Same data as the R package.

## Reference

Xiao, N. and Chun, Y. (2009). Visualizing migration flows using kriskograms. *Cartography and Geographic Information Science*, 36(2), 183–191. https://doi.org/10.1559/152304009788188763

## Credits

Original R package and method by **Sohyun Park** and **Ningchuan Xiao**. Python rewrite built with the help of **Anthropic Claude**, verified against the R implementation's geometry and mean-centre formulas.

## License

MIT — see [LICENSE](LICENSE).
