# Investment System Audit

Investment system audit inspected 17 expected file(s), found 12, and scanned 30953 total row(s). Warning count: 8.

## Warnings

- Missing values detected in output/leader_laggard_summary.csv.
- Missing values detected in output/forward_outcomes.csv.
- Missing values detected in output/pre_signal_raw.csv.
- Missing values detected in output/pre_signal_candidates.csv.
- Missing values detected in output/pre_signal_candidates_v5.csv.
- Missing values detected in output/pre_signal_candidates_excess.csv.
- Missing values detected in output/backfilled_live_signals_v5.csv.
- Small sample size in output/v32_ab_live_signal_snapshot.csv: 1 rows.

## File Inventory

### price_data

- `output/price_data.csv` ? `ok` rows=`6743`
- `output/btc_price_data.csv` ? `ok` rows=`2281`
- `output/eth_price_data.csv` ? `ok` rows=`2281`
- `output/sol_price_data.csv` ? `ok` rows=`2181`

### leader_laggard

- `output/leader_laggard_summary.csv` ? `ok` rows=`2180`

### forward_outcomes

- `output/forward_outcomes.csv` ? `ok` rows=`6527`

### pre_signal

- `output/pre_signal_raw.csv` ? `ok` rows=`2178`
- `output/pre_signal_candidates.csv` ? `ok` rows=`2178`
- `output/pre_signal_candidates_v5.csv` ? `ok` rows=`2178`
- `output/pre_signal_candidates_excess.csv` ? `ok` rows=`2178`

### live_signals

- `output/live_signal_v5.csv` ? `missing` rows=`n/a`
- `output/backfilled_live_signals_v5.csv` ? `ok` rows=`47`
- `output/v32_ab_live_signal_snapshot.csv` ? `ok` rows=`1`
- `output/v32_ab_live_execution.csv` ? `missing` rows=`n/a`

### equity

- `output/equity_curve_v5.csv` ? `missing` rows=`n/a`
- `output/equity_compare_summary_v5.csv` ? `missing` rows=`n/a`
- `output/equity_compare_trades_v5.csv` ? `missing` rows=`n/a`

## Signals

- Signal files found: `6`
- `output/backfilled_live_signals_v5.csv` rows=`47`
- `output/v32_ab_live_signal_snapshot.csv` rows=`1`
- `output/pre_signal_raw.csv` rows=`2178`
- `output/pre_signal_candidates.csv` rows=`2178`
- `output/pre_signal_candidates_v5.csv` rows=`2178`
- `output/pre_signal_candidates_excess.csv` rows=`2178`

## Forward Returns

### output/backfilled_live_signals_v5.csv

#### fwd_return_hold_72
- Count: `47`
- Win rate > 0: `0.76595745`
- Mean: `115.39978546`
- Median: `39.04773627`
- Min: `-40.79912705`
- Max: `860.12893777`

#### fwd_return_hold_96
- Count: `47`
- Win rate > 0: `0.72340426`
- Mean: `156.46873234`
- Median: `60.10664267`
- Min: `-50.23059545`
- Max: `1337.05884564`

#### fwd_return_hold_144
- Count: `47`
- Win rate > 0: `0.76595745`
- Mean: `286.82906459`
- Median: `124.89864648`
- Min: `-57.34867221`
- Max: `3768.19191122`

#### fwd_return_hold_192
- Count: `47`
- Win rate > 0: `0.80851064`
- Mean: `366.14419024`
- Median: `229.2863836`
- Min: `-76.27568971`
- Max: `2348.77590499`

#### fwd_return_hold_288
- Count: `46`
- Win rate > 0: `0.82608696`
- Mean: `1239.68693769`
- Median: `381.19043443`
- Min: `-78.68780752`
- Max: `10749.97321632`

#### BTC-USD_ret_1d
- Count: `47`
- Win rate > 0: `0.4893617`
- Mean: `0.00268091`
- Median: `-4.332e-05`
- Min: `-0.09930199`
- Max: `0.10961007`

#### BTC-USD_ret_3d
- Count: `47`
- Win rate > 0: `0.5106383`
- Mean: `0.01119998`
- Median: `0.00883`
- Min: `-0.13122709`
- Max: `0.13313257`

#### BTC-USD_ret_5d
- Count: `47`
- Win rate > 0: `0.65957447`
- Mean: `0.02513122`
- Median: `0.0087023`
- Min: `-0.1479296`
- Max: `0.21979659`

#### ETH-USD_ret_1d
- Count: `47`
- Win rate > 0: `0.59574468`
- Mean: `0.00655742`
- Median: `0.01138606`
- Min: `-0.11884948`
- Max: `0.10100812`

#### ETH-USD_ret_3d
- Count: `47`
- Win rate > 0: `0.63829787`
- Mean: `0.02573718`
- Median: `0.01176659`
- Min: `-0.17188014`
- Max: `0.16600392`

#### ETH-USD_ret_5d
- Count: `47`
- Win rate > 0: `0.65957447`
- Mean: `0.05899939`
- Median: `0.0296542`
- Min: `-0.18683904`
- Max: `0.38398988`

#### SOL-USD_ret_1d
- Count: `47`
- Win rate > 0: `0.57446809`
- Mean: `0.02361692`
- Median: `0.00896237`
- Min: `-0.09227518`
- Max: `0.19582044`

#### SOL-USD_ret_3d
- Count: `47`
- Win rate > 0: `0.70212766`
- Mean: `0.04625092`
- Median: `0.02557503`
- Min: `-0.25796059`
- Max: `0.41441979`

#### SOL-USD_ret_5d
- Count: `47`
- Win rate > 0: `0.63829787`
- Mean: `0.0869177`
- Median: `0.05185869`
- Min: `-0.17788975`
- Max: `0.70353226`

### output/forward_outcomes.csv

#### fwd_return_hold_72
- Count: `6527`
- Win rate > 0: `0.56672284`
- Mean: `28.34779925`
- Median: `7.00922364`
- Min: `-78.67427891`
- Max: `1039.35774889`

#### fwd_return_hold_96
- Count: `6455`
- Win rate > 0: `0.57846631`
- Mean: `42.70056028`
- Median: `9.47545808`
- Min: `-72.42545821`
- Max: `1551.80877791`

#### fwd_return_hold_144
- Count: `6311`
- Win rate > 0: `0.59958802`
- Mean: `74.20867423`
- Median: `16.23862404`
- Min: `-77.83711422`
- Max: `3814.83284982`

#### fwd_return_hold_192
- Count: `6167`
- Win rate > 0: `0.65185666`
- Mean: `106.78449096`
- Median: `25.07316046`
- Min: `-86.86145938`
- Max: `3258.96838627`

#### fwd_return_hold_288
- Count: `5879`
- Win rate > 0: `0.70011907`
- Mean: `291.15425634`
- Median: `40.58623359`
- Min: `-89.72572997`
- Max: `12696.06916221`

