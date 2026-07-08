# Alpha Backtest Sanity Audit

Alpha sanity audit scanned 33416 trade row(s) across 34 hypothesis/hypotheses.

## Warnings

- Extreme positive return above 1000% detected. Verify return scale and data integrity.
- momentum_top_rank_288_q90: non-overlapping trade count is very small versus raw count.
- momentum_top_rank_288_q90: performance sample is highly concentrated in SOL-USD.
- breadth_dispersion_breakout_288: non-overlapping trade count is very small versus raw count.
- breadth_dispersion_breakout_288: performance sample is highly concentrated in SOL-USD.
- breadth_positive_288_0_8: non-overlapping trade count is very small versus raw count.
- breadth_positive_288_0_8: performance sample is highly concentrated in SOL-USD.
- breadth_positive_288_1_0: non-overlapping trade count is very small versus raw count.
- breadth_positive_288_1_0: performance sample is highly concentrated in SOL-USD.
- momentum_top_rank_288_q75: non-overlapping trade count is very small versus raw count.
- momentum_top_rank_288_q75: performance sample is highly concentrated in SOL-USD.
- breadth_positive_288_0_5: non-overlapping trade count is very small versus raw count.
- breadth_positive_288_0_66: non-overlapping trade count is very small versus raw count.
- momentum_top_rank_288_q50: non-overlapping trade count is very small versus raw count.
- leader_persistence_288_3: non-overlapping trade count is very small versus raw count.
- leader_persistence_288_8: non-overlapping trade count is very small versus raw count.
- momentum_top_rank_72_q90: performance sample is highly concentrated in SOL-USD.

## Overall

- Trades: `33416`
- Win rate: `0.600341`
- Mean: `0.70623415`
- Median: `0.10080634`
- Min: `-0.8972573`
- Max: `46.54075418`
- >100% count: `6506`
- >500% count: `1101`

## Non-Overlapping Overall

- Trades: `2137`
- Win rate: `0.547964`
- Mean: `0.15039832`
- Median: `0.02383795`
- Min: `-0.89403426`
- Max: `6.83071756`

## Top Hypothesis Sanity

### momentum_top_rank_288_q90

- Trades: `465`
- Win rate: `0.554839`
- Mean: `2.52234656`
- Median: `0.26688097`
- Min: `-0.87432117`
- Max: `46.54075418`
- Non-overlap trades: `43`
- Non-overlap mean: `2.88294428`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 438, 'ETH-USD': 27}`

### breadth_dispersion_breakout_288

- Trades: `499`
- Win rate: `0.527054`
- Mean: `2.06298463`
- Median: `0.06585338`
- Min: `-0.87432117`
- Max: `40.52157704`
- Non-overlap trades: `44`
- Non-overlap mean: `2.55062397`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 499}`

### breadth_positive_288_0_8

- Trades: `983`
- Win rate: `0.685656`
- Mean: `2.00766686`
- Median: `0.5534458`
- Min: `-0.89198904`
- Max: `46.54075418`
- Non-overlap trades: `94`
- Non-overlap mean: `2.14921472`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 802, 'ETH-USD': 108, 'BTC-USD': 73}`

### breadth_positive_288_1_0

- Trades: `983`
- Win rate: `0.685656`
- Mean: `2.00766686`
- Median: `0.5534458`
- Min: `-0.89198904`
- Max: `46.54075418`
- Non-overlap trades: `94`
- Non-overlap mean: `2.14921472`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 802, 'ETH-USD': 108, 'BTC-USD': 73}`

### leadership_rotation_breakout_72

- Trades: `4`
- Win rate: `1.0`
- Mean: `1.92550633`
- Median: `1.82943586`
- Min: `0.30168203`
- Max: `3.74147156`
- Non-overlap trades: `4`
- Non-overlap mean: `1.92550633`
- Duplicate trades: `0`
- Asset counts: `{'ETH-USD': 2, 'SOL-USD': 2}`

### momentum_top_rank_288_q75

- Trades: `809`
- Win rate: `0.599506`
- Mean: `1.88068833`
- Median: `0.32428743`
- Min: `-0.8972573`
- Max: `46.54075418`
- Non-overlap trades: `74`
- Non-overlap mean: `2.20442813`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 724, 'ETH-USD': 84, 'BTC-USD': 1}`

### breadth_positive_288_0_5

- Trades: `1281`
- Win rate: `0.654957`
- Mean: `1.60210373`
- Median: `0.34887528`
- Min: `-0.8972573`
- Max: `46.54075418`
- Non-overlap trades: `117`
- Non-overlap mean: `1.78536725`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 884, 'BTC-USD': 253, 'ETH-USD': 144}`

### breadth_positive_288_0_66

- Trades: `1281`
- Win rate: `0.654957`
- Mean: `1.60210373`
- Median: `0.34887528`
- Min: `-0.8972573`
- Max: `46.54075418`
- Non-overlap trades: `117`
- Non-overlap mean: `1.78536725`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 884, 'BTC-USD': 253, 'ETH-USD': 144}`

### momentum_top_rank_288_q50

- Trades: `1265`
- Win rate: `0.61502`
- Mean: `1.54489779`
- Median: `0.22159383`
- Min: `-0.8972573`
- Max: `46.54075418`
- Non-overlap trades: `116`
- Non-overlap mean: `1.74666448`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 911, 'BTC-USD': 213, 'ETH-USD': 141}`

### leader_persistence_288_3

- Trades: `1643`
- Win rate: `0.686549`
- Mean: `1.20282013`
- Median: `0.28328322`
- Min: `-0.8972573`
- Max: `36.84813127`
- Non-overlap trades: `147`
- Non-overlap mean: `1.31240653`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 907, 'BTC-USD': 452, 'ETH-USD': 284}`

### leader_persistence_288_8

- Trades: `1540`
- Win rate: `0.676623`
- Mean: `1.09262675`
- Median: `0.27206468`
- Min: `-0.8972573`
- Max: `27.45738499`
- Non-overlap trades: `136`
- Non-overlap mean: `1.23231271`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 879, 'BTC-USD': 407, 'ETH-USD': 254}`

### topology_low_density_leader_72

- Trades: `633`
- Win rate: `0.71406`
- Mean: `0.59543661`
- Median: `0.43922732`
- Min: `-0.6210063`
- Max: `4.51286557`
- Non-overlap trades: `224`
- Non-overlap mean: `0.60674584`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 420, 'BTC-USD': 123, 'ETH-USD': 90}`

### breadth_dispersion_breakout_72

- Trades: `539`
- Win rate: `0.688312`
- Mean: `0.57517605`
- Median: `0.42641687`
- Min: `-0.6210063`
- Max: `4.51286557`
- Non-overlap trades: `193`
- Non-overlap mean: `0.59054397`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 407, 'ETH-USD': 72, 'BTC-USD': 60}`

### momentum_top_rank_72_q90

- Trades: `482`
- Win rate: `0.665975`
- Mean: `0.49523579`
- Median: `0.35950884`
- Min: `-0.6210063`
- Max: `4.51286557`
- Non-overlap trades: `176`
- Non-overlap mean: `0.50941244`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 412, 'ETH-USD': 49, 'BTC-USD': 21}`

### momentum_top_rank_72_q75

- Trades: `871`
- Win rate: `0.61194`
- Mean: `0.43058575`
- Median: `0.22394951`
- Min: `-0.64978076`
- Max: `4.51286557`
- Non-overlap trades: `310`
- Non-overlap mean: `0.43469049`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 574, 'ETH-USD': 196, 'BTC-USD': 101}`

### momentum_top_rank_72_q50

- Trades: `1344`
- Win rate: `0.572917`
- Mean: `0.37929796`
- Median: `0.08888538`
- Min: `-0.69268408`
- Max: `4.80183044`
- Non-overlap trades: `490`
- Non-overlap mean: `0.37945142`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 775, 'ETH-USD': 310, 'BTC-USD': 259}`

### breadth_positive_72_0_66

- Trades: `1277`
- Win rate: `0.570869`
- Mean: `0.3542796`
- Median: `0.08539195`
- Min: `-0.69268408`
- Max: `4.51286557`
- Non-overlap trades: `475`
- Non-overlap mean: `0.34891834`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 743, 'ETH-USD': 291, 'BTC-USD': 243}`

### breadth_positive_72_0_5

- Trades: `1293`
- Win rate: `0.573086`
- Mean: `0.35152689`
- Median: `0.08568239`
- Min: `-0.69268408`
- Max: `4.51286557`
- Non-overlap trades: `481`
- Non-overlap mean: `0.34682982`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 743, 'ETH-USD': 294, 'BTC-USD': 256}`

### breadth_positive_72_0_8

- Trades: `963`
- Win rate: `0.553479`
- Mean: `0.3381266`
- Median: `0.06810408`
- Min: `-0.69268408`
- Max: `4.51286557`
- Non-overlap trades: `365`
- Non-overlap mean: `0.33502806`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 616, 'ETH-USD': 233, 'BTC-USD': 114}`

### breadth_positive_72_1_0

- Trades: `963`
- Win rate: `0.553479`
- Mean: `0.3381266`
- Median: `0.06810408`
- Min: `-0.69268408`
- Max: `4.51286557`
- Non-overlap trades: `365`
- Non-overlap mean: `0.33502806`
- Duplicate trades: `0`
- Asset counts: `{'SOL-USD': 616, 'ETH-USD': 233, 'BTC-USD': 114}`

## Extreme Top Trades

- `{'hypothesis_id': 'breadth_positive_288_0_66', 'family': 'breadth', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'momentum_top_rank_288_q50', 'family': 'momentum', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'breadth_positive_288_1_0', 'family': 'breadth', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'momentum_top_rank_288_q75', 'family': 'momentum', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'breadth_positive_288_0_5', 'family': 'breadth', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'momentum_top_rank_288_q90', 'family': 'momentum', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'breadth_positive_288_0_8', 'family': 'breadth', 'date': '2021-02-01', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 46.54075417501187}`
- `{'hypothesis_id': 'breadth_dispersion_breakout_288', 'family': 'breadth', 'date': '2021-02-02', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 40.52157704088029}`
- `{'hypothesis_id': 'momentum_top_rank_288_q90', 'family': 'momentum', 'date': '2021-02-02', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 40.52157704088029}`
- `{'hypothesis_id': 'breadth_positive_288_0_5', 'family': 'breadth', 'date': '2021-02-02', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': 40.52157704088029}`

## Extreme Worst Trades

- `{'hypothesis_id': 'leader_persistence_288_3', 'family': 'leadership', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'momentum_top_rank_288_q50', 'family': 'momentum', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'momentum_top_rank_288_q75', 'family': 'momentum', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'breadth_positive_288_0_66', 'family': 'breadth', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'breadth_positive_288_0_5', 'family': 'breadth', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'leader_persistence_288_8', 'family': 'leadership', 'date': '2022-02-06', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8972572997180492}`
- `{'hypothesis_id': 'leader_persistence_288_3', 'family': 'leadership', 'date': '2022-02-07', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8940342604921839}`
- `{'hypothesis_id': 'breadth_positive_288_0_5', 'family': 'breadth', 'date': '2022-02-07', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8940342604921839}`
- `{'hypothesis_id': 'leader_persistence_288_8', 'family': 'leadership', 'date': '2022-02-07', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8940342604921839}`
- `{'hypothesis_id': 'breadth_positive_288_0_66', 'family': 'breadth', 'date': '2022-02-07', 'asset': 'SOL-USD', 'direction': 'LONG', 'hold_period': 288, 'return': -0.8940342604921839}`
