[English](README.md) | **한국어**

# halfcircle

양방향 흐름 데이터를 한눈에 읽는 도구.

![같은 교역 흐름을 1인당 GDP 순과 인구 순으로 배열한 두 개의 반원 다이어그램](preview.png)

노드를 원의 중심선 위에 늘어놓고, 각 흐름을 출발지에서 도착지로 **시계방향 반원**으로 그립니다. 그래서 A→B와 B→A는 반대쪽으로 부풀어 서로 겹치지 않습니다. 노드 순서를 바꾸면 그림이 흩어지거나 한 방향으로 정렬되는데, **그 비교가 곧 분석입니다.**

2018년 CRAN에 올린 [동명의 R 패키지](https://cran.r-project.org/src/contrib/Archive/halfcircle/)(Park & Xiao)를 파이썬으로 다시 쓰고, 정렬을 체계적으로 비교하는 기능을 더했습니다.

## 설치

```bash
pip install git+https://github.com/wherewindstay/halfcircle.git
```

## 기본 사용법

```python
from halfcircle import halfcircle, load_trade

flow, node = load_trade()                    # 작물 교역에 내재된 토지, 154개국
flow = flow.loc[flow["vegetable"] > 5000, ["O", "D", "vegetable"]]
node = node.sort_values("gdpc", ascending=False)

halfcircle(flow, node, orientation="vertical", labels=False, drop_missing=True)
```

`flow`는 열 위치로 읽습니다 — 출발지, 도착지, 크기. R 패키지에 쓰던 파일을 그대로 넣을 수 있습니다.

## 어떤 순서가 의미 있는지 찾기

이 다이어그램은 순서를 바꿔 비교해야 말을 합니다. `compare_orders`는 그 비교를 수치로 합니다 — 각 정렬에서 모든 반원의 평균중심이 원점에서 얼마나 벗어나는지 알려줍니다. 원점에 가까우면 흐름이 상쇄된다는 뜻이고, 한쪽으로 크게 밀리면 물량이 일관되게 한 방향으로 흐른다는 뜻입니다.

```python
from halfcircle import compare_orders

compare_orders(flow, {
    "1인당 GDP": node.sort_values("gdpc", ascending=False),
    "인구":      node.sort_values("pop_total", ascending=False),
    "경작면적":  node.sort_values("area_cultivation", ascending=False),
    "알파벳순":  node.sort_values("country"),
}, drop_missing=True)
```

```
    order  x_weighted  y_weighted  distance
       인구   -0.722115    0.006337  0.722143
     경작면적   -0.632828    0.028257  0.633458
  1인당 GDP   -0.415186   -0.077493  0.422356
     알파벳순    0.080736    0.061077  0.101236
```

인구 순으로 배열했을 때 평균중심이 가장 멀리(0.72) 밀려나고, 알파벳순은 원점 근처(0.10)에 머뭅니다 — 의미 없는 정렬이라면 마땅히 그래야 합니다. 이 흐름을 조직하는 축은 소득이 아니라 인구라는 뜻입니다.

읽는 대신 보고 싶다면:

```python
from halfcircle import inspect

inspect(flow, {"1인당 GDP": node.sort_values("gdpc", ascending=False),
               "인구":      node.sort_values("pop_total", ascending=False)},
        orientation="vertical", labels=False, drop_missing=True)
```

각 패널에 평균중심까지의 거리가 표시되고 그 위치가 붉은 점으로 찍힙니다.

## 함수

| 함수 | 하는 일 |
|---|---|
| `halfcircle(flow, nodes, ...)` | 다이어그램을 그리고 matplotlib `Axes`를 반환 |
| `inspect(flow, orders, ...)` | 같은 흐름을 여러 정렬로 나란히 그림 |
| `mean_center(flow, nodes, ...)` | 모든 반원의 가중·비가중 평균중심 |
| `compare_orders(flow, orders, ...)` | 여러 정렬의 평균중심을 거리순으로 비교 |
| `plot_mean_center(flow, nodes, ...)` | 다이어그램을 평균중심 두 점으로 축약 |
| `node_positions`, `arc_points`, `flow_arcs` | 기하 계산만 — 직접 그리고 싶을 때 |
| `load_trade()`, `load_flow()`, `load_nodes()` | 동봉된 예제 데이터 |

`flow_color`, `flow_width`, `node_color`, `labels`는 R 패키지와 같이 단일 값 또는 행마다 하나씩 받습니다. 속성별로 색을 나누거나 특정 노드만 강조할 수 있습니다.

```python
# 한 나라가 걸린 흐름만 강조
colors = ["crimson" if "China" in (o, d) else "lightgray"
          for o, d in zip(flow["O"], flow["D"])]
halfcircle(flow, node, flow_color=colors, orientation="vertical", labels=False)
```

## 알아둘 점

- 자기 자신으로 가는 흐름(출발지=도착지)은 그리지 않고, 평균중심 계산에서도 뺍니다.
- `flow`에는 있는데 `nodes`에 없는 노드가 있으면 오류를 냅니다. 건너뛰려면 `drop_missing=True`를 주세요.
- `flow_width="proportional"`은 선 굵기를 물량에 비례시키되 최대 10포인트로 제한합니다. R 원본과 같습니다.

## 예제 데이터

`load_trade()`는 154개국 사이 작물 교역에 내재된 토지(10,866쌍 · 채소·과일·밀·대두, 헥타르)와, 정렬 기준으로 쓸 국가 속성(좌표·인구·1인당 GDP·경작면적·물 사용량·소득수준)을 함께 돌려줍니다. R 패키지와 같은 데이터입니다.

## 참고문헌

Xiao, N. and Chun, Y. (2009). Visualizing migration flows using kriskograms. *Cartography and Geographic Information Science*, 36(2), 183–191. https://doi.org/10.1559/152304009788188763

## 만든 사람

원 R 패키지와 방법론은 **박소현**, **Ningchuan Xiao**. 파이썬 재작성은 Anthropic Claude의 도움을 받아 진행했고, R 구현의 기하 계산과 평균중심 공식을 대조해 검증했습니다.

## 라이선스

MIT — [LICENSE](LICENSE) 참조.
