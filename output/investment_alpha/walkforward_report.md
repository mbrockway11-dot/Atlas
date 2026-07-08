# Walk-Forward Alpha Report

Walk-forward Alpha v1.2 evaluated 8 split(s). Exposure: 0.2. Drawdown control: True. Stability score: 0.6. Aggregate test avg return: 0.04221872.

## Parameters

```json
{
  "train_days": 730,
  "test_days": 180,
  "step_days": 180,
  "top_n": 5,
  "min_train_trades": 30,
  "exposure": 0.2,
  "drawdown_control": true
}
```

## Aggregate Test

```json
{
  "count": 93,
  "win_rate": 0.645161,
  "avg_return": 0.04221872,
  "median_return": 0.01957537,
  "profit_factor": 3.678888,
  "max_drawdown": -0.53796879,
  "sharpe_like": 4.51556,
  "final_equity": 33.26311095,
  "exposure": 0.2,
  "drawdown_control": true,
  "avg_raw_return_capped": 0.23095454,
  "max_raw_return_capped": 2.08942153,
  "min_raw_return_capped": -0.89241926,
  "max_position_return": 0.30914582,
  "min_position_return": -0.17848385
}
```

## Splits

### wf_001

- Train: `2020-01-25 00:00:00` -> `2022-01-24 00:00:00`
- Test: `2022-01-24 00:00:00` -> `2022-07-23 00:00:00`
- Selected: `['breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'breadth_positive_288_0_5', 'breadth_positive_288_0_66', 'momentum_top_rank_288_q50']`
- Raw test count: `416`
- Non-overlap test count: `10`
- Test metrics: `{'count': 10, 'win_rate': 0.0, 'avg_return': -0.0852188, 'median_return': -0.08567136, 'profit_factor': 0.0, 'max_drawdown': -0.52591439, 'sharpe_like': -5.154856, 'final_equity': 0.40425602, 'exposure': 0.2, 'drawdown_control': True, 'avg_raw_return_capped': -0.78700437, 'max_raw_return_capped': -0.48408273, 'min_raw_return_capped': -0.89241926, 'max_position_return': -0.02420414, 'min_position_return': -0.17848385}`

### wf_002

- Train: `2020-07-23 00:00:00` -> `2022-07-23 00:00:00`
- Test: `2022-07-23 00:00:00` -> `2023-01-19 00:00:00`
- Selected: `['breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'momentum_top_rank_288_q90', 'breadth_dispersion_breakout_288', 'breadth_positive_288_0_5']`
- Raw test count: `0`
- Non-overlap test count: `0`
- Test metrics: `{'count': 0, 'win_rate': None, 'avg_return': None, 'median_return': None, 'profit_factor': None, 'max_drawdown': None, 'sharpe_like': None, 'final_equity': None, 'exposure': 0.2, 'drawdown_control': True}`

### wf_003

- Train: `2021-01-19 00:00:00` -> `2023-01-19 00:00:00`
- Test: `2023-01-19 00:00:00` -> `2023-07-18 00:00:00`
- Selected: `['momentum_top_rank_288_q90', 'breadth_dispersion_breakout_288', 'breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'momentum_top_rank_288_q75']`
- Raw test count: `0`
- Non-overlap test count: `0`
- Test metrics: `{'count': 0, 'win_rate': None, 'avg_return': None, 'median_return': None, 'profit_factor': None, 'max_drawdown': None, 'sharpe_like': None, 'final_equity': None, 'exposure': 0.2, 'drawdown_control': True}`

### wf_004

- Train: `2021-07-18 00:00:00` -> `2023-07-18 00:00:00`
- Test: `2023-07-18 00:00:00` -> `2024-01-14 00:00:00`
- Selected: `['breadth_dispersion_breakout_72', 'breadth_positive_72_0_8', 'breadth_positive_72_1_0', 'momentum_top_rank_72_q90', 'momentum_top_rank_72_q75']`
- Raw test count: `426`
- Non-overlap test count: `35`
- Test metrics: `{'count': 35, 'win_rate': 0.828571, 'avg_return': 0.12663509, 'median_return': 0.13144681, 'profit_factor': 44.167026, 'max_drawdown': -0.05762862, 'sharpe_like': 7.227995, 'final_equity': 56.38569025, 'exposure': 0.2, 'drawdown_control': True, 'avg_raw_return_capped': 0.63317547, 'max_raw_return_capped': 2.08942153, 'min_raw_return_capped': -0.21871191, 'max_position_return': 0.41788431, 'min_position_return': -0.04374238}`

### wf_005

- Train: `2022-01-14 00:00:00` -> `2024-01-14 00:00:00`
- Test: `2024-01-14 00:00:00` -> `2024-07-12 00:00:00`
- Selected: `['breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'breadth_positive_288_0_5', 'breadth_positive_288_0_66', 'momentum_top_rank_288_q50']`
- Raw test count: `900`
- Non-overlap test count: `15`
- Test metrics: `{'count': 15, 'win_rate': 0.666667, 'avg_return': 0.08026405, 'median_return': 0.06969154, 'profit_factor': 8.753348, 'max_drawdown': -0.14659046, 'sharpe_like': 2.714143, 'final_equity': 2.94943367, 'exposure': 0.2, 'drawdown_control': True, 'avg_raw_return_capped': 0.40132023, 'max_raw_return_capped': 1.5457291, 'min_raw_return_capped': -0.24936354, 'max_position_return': 0.30914582, 'min_position_return': -0.04987271}`

### wf_006

- Train: `2022-07-13 00:00:00` -> `2024-07-12 00:00:00`
- Test: `2024-07-12 00:00:00` -> `2025-01-08 00:00:00`
- Selected: `['breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'breadth_positive_288_0_5', 'breadth_positive_288_0_66', 'momentum_top_rank_288_q50']`
- Raw test count: `841`
- Non-overlap test count: `18`
- Test metrics: `{'count': 18, 'win_rate': 0.833333, 'avg_return': 0.02949129, 'median_return': 0.0145659, 'profit_factor': 10.615229, 'max_drawdown': -0.03913209, 'sharpe_like': 2.503336, 'final_equity': 1.65552115, 'exposure': 0.2, 'drawdown_control': True, 'avg_raw_return_capped': 0.14745647, 'max_raw_return_capped': 0.86949214, 'min_raw_return_capped': -0.15314406, 'max_position_return': 0.17389843, 'min_position_return': -0.03062881}`

### wf_007

- Train: `2023-01-09 00:00:00` -> `2025-01-08 00:00:00`
- Test: `2025-01-08 00:00:00` -> `2025-07-07 00:00:00`
- Selected: `['breadth_positive_288_0_5', 'breadth_positive_288_0_66', 'momentum_top_rank_288_q50', 'leader_persistence_288_3', 'breadth_positive_288_0_8']`
- Raw test count: `441`
- Non-overlap test count: `15`
- Test metrics: `{'count': 15, 'win_rate': 0.4, 'avg_return': -0.01737571, 'median_return': -0.01180785, 'profit_factor': 0.309231, 'max_drawdown': -0.30416618, 'sharpe_like': -1.807523, 'final_equity': 0.7610819, 'exposure': 0.2, 'drawdown_control': True, 'avg_raw_return_capped': -0.09908967, 'max_raw_return_capped': 0.15839685, 'min_raw_return_capped': -0.37487897, 'max_position_return': 0.03167937, 'min_position_return': -0.06825947}`

### wf_008

- Train: `2023-07-08 00:00:00` -> `2025-07-07 00:00:00`
- Test: `2025-07-07 00:00:00` -> `2026-01-03 00:00:00`
- Selected: `['breadth_positive_288_0_8', 'breadth_positive_288_1_0', 'breadth_positive_288_0_5', 'breadth_positive_288_0_66', 'momentum_top_rank_288_q50']`
- Raw test count: `0`
- Non-overlap test count: `0`
- Test metrics: `{'count': 0, 'win_rate': None, 'avg_return': None, 'median_return': None, 'profit_factor': None, 'max_drawdown': None, 'sharpe_like': None, 'final_equity': None, 'exposure': 0.2, 'drawdown_control': True}`
