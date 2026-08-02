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

## Is the pattern real?

A diagram always looks like *something*. `order_significance` asks whether your ordering beats an arbitrary one: it shuffles the nodes hundreds of times, builds the null distribution of mean-centre offsets, and reports where the real ordering falls.

```python
from halfcircle import order_significance

res = order_significance(flow, node.sort_values("income_level"),
                         orientation="vertical", n_permutations=999,
                         drop_missing=True)
print(res.summary())
```

```
mean centre 0.419 from origin (random orderings: 0.115 ± 0.073) — p = 0.0033, stronger than chance
```

The two components are tested separately too, because they mean different things. With `orientation="vertical"`, `p_x` covers **directional imbalance** — how consistently volume runs one way along the ordering — and `p_y` covers **where along the ordering** flows concentrate. In the run above `p_y = 0.003` while `p_x = 0.27`: income level governs *which* countries trade, but not the direction.

### Do two flows differ?

Cereals against vegetables, or the same commodity a decade apart — same question, same test. `compare_flows` pools every edge, splits it at random keeping group sizes, and asks how often the two mean centres land as far apart as they really are.

```python
from halfcircle import compare_flows

res = compare_flows(vegetables, cereals, node.sort_values("income_level"),
                    label_a="vegetables", label_b="cereals",
                    orientation="vertical", drop_missing=True)
print(res.summary())
```

```
vegetables (0.419) and cereals (0.225) differ: centres 0.237 apart, p = 0.0167
```

## Following a flow field over time

Park, Munroe and Xiao (2023) read four decades of cereal trade by drawing one diagram per period. `track` makes that comparison numeric — each period collapses to its mean centre, and the path those points trace is the finding.

```python
from halfcircle import track, plot_track

periods = {"1988-90": f1, "1998-00": f2, "2008-10": f3, "2018-20": f4}
track(periods, node.sort_values("income_level"), orientation="vertical")
```

Each row carries the mean centre, its distance from the origin, how far it moved since the previous period, and the two components split out as `skew_axis` (directional imbalance) and `spread_axis` (position along the ordering). `plot_track` draws the path, with later periods as larger dots.

## API

| Function | What it does |
|---|---|
| `halfcircle(flow, nodes, ...)` | Draw the diagram, return a matplotlib `Axes` |
| `inspect(flow, orders, ...)` | Draw the same flows under several orderings, side by side |
| `mean_center(flow, nodes, ...)` | Weighted and unweighted mean centre of every arc |
| `compare_orders(flow, orders, ...)` | Mean centres for several orderings, ranked by distance |
| `plot_mean_center(flow, nodes, ...)` | The diagram reduced to its two mean-centre points |
| `order_significance(flow, nodes, ...)` | Permutation test: does this ordering beat a random one? |
| `compare_flows(a, b, nodes, ...)` | Permutation test: are two flow variables organised differently? |
| `track(periods, nodes, ...)` | Mean centre per period, with movement between them |
| `plot_track(periods, nodes, ...)` | Draw the path the mean centre traces over time |
| `node_positions`, `arc_points`, `flow_arcs` | Geometry only, if you want to draw it yourself |
| `load_trade()`, `load_flow()`, `load_nodes()` | The bundled example data |

Styling follows the R package: `flow_color`, `flow_width`, `node_color` and `labels` each take a single value or one value per row, so you can colour arcs by attribute or highlight a single node.

## More examples

**Highlight one country's flows**

```python
colors = ["crimson" if "China" in (o, d) else "#dddddd"
          for o, d in zip(flow["O"], flow["D"])]
halfcircle(flow, node, flow_color=colors, orientation="vertical", labels=False)
```

**Colour arcs by an attribute of the origin**

```python
palette = {"1. High income": "#22abcb", "2. Upper middle income": "#4eb6ad",
           "3. Middle income": "#86c388", "4. Lower middle income": "#adcd6c",
           "5. Low income": "#dad84f"}
lookup = node.set_index("country")["income_level"].map(palette)
halfcircle(flow, node, flow_color=[lookup.get(o, "gray") for o in flow["O"]],
           orientation="vertical", labels=False)
```

**Label only the countries you care about**

```python
watch = {"China", "United States", "Brazil"}
halfcircle(flow, node, labels=[n if n in watch else "" for n in node["country"]],
           label_size=7, orientation="vertical")
```

**Compare commodities side by side**

```python
inspect({"vegetable": veg, "wheat": wheat, "soybean": soy}, ...)  # see inspect() for orderings
```

**Use the geometry without matplotlib**

```python
from halfcircle import flow_arcs
for arc in flow_arcs(flow, node, orientation="vertical"):
    ...  # arc.x, arc.y, arc.volume, arc.radius — feed them to any renderer
```

## The original R package

The 2018 CRAN release is archived, and its source tarball is kept in [`r-legacy/`](r-legacy/) so it stays installable:

```r
install.packages("r-legacy/halfcircle_0.1.0.tar.gz", repos = NULL, type = "source")
```

## Notes

- Self-flows (origin equal to destination) are not drawn, and are excluded from the mean centre.
- Nodes appearing in `flow` but missing from `nodes` raise an error; pass `drop_missing=True` to skip them instead.
- `flow_width="proportional"` scales linewidth to volume, capped at 10 points, matching the R original.

## Example data

`load_trade()` returns land embodied in crop trade between 154 countries (10,866 pairs; vegetable, fruit, wheat and soybean, in hectares) together with country attributes — coordinates, population, GDP per capita, cultivated area, water use and income level — to sort by. Same data as the R package.

## References

Park, S., Munroe, D. K. and Xiao, N. (2023). Visualizing economic drivers of virtual land trade: A case study of global cereals trade. *Environment and Planning B: Urban Analytics and City Science*, 50(9). https://doi.org/10.1177/23998083231177057 — halfcircle diagrams applied to four decades of cereal trade.

Xiao, N. and Chun, Y. (2009). Visualizing migration flows using kriskograms. *Cartography and Geographic Information Science*, 36(2), 183–191. https://doi.org/10.1559/152304009788188763 — the method this package implements.

## Credits

Original R package and method by **Sohyun Park** and **Ningchuan Xiao**. Python rewrite built with the help of **Anthropic Claude**, verified against the R implementation's geometry and mean-centre formulas.

## License

MIT — see [LICENSE](LICENSE).
