# The original R package

`halfcircle` was published to CRAN in 2018 and later archived. The source tarball
is kept here so the R version stays installable — CRAN archives can move, and a
paper that cites the package should not depend on a URL staying alive.

## Install locally

```r
install.packages("halfcircle_0.1.0.tar.gz", repos = NULL, type = "source")
```

```r
library(halfcircle)
data(ex_flow); data(ex_node)
flow <- subset(ex_flow[, c(1, 2, 3)], vegetable > 5000)
node <- ex_node[order(-ex_node$gdpc), ]
halfcircle(flow, node, dir = "vertical", circle.col = "gray",
           flow.col = "black", label = NULL)
```

Dependencies: `scales`, `graphics`.

## What it contains

Two functions — `halfcircle()` draws the diagram, `halfmeancenter()` computes and
plots the weighted and unweighted mean centres — plus the `ex_flow` and `ex_node`
example datasets.

The Python package in the parent directory reproduces both functions exactly
(same node spacing, arc geometry, line-width scaling and 4r/3π centroid formula)
and adds significance testing, ordering comparison and time-series tracking.

## Citation

Park, S. and Xiao, N. (2018). *halfcircle: Plot Halfcircle Diagram.* R package
version 0.1.0. https://cran.r-project.org/src/contrib/Archive/halfcircle/
