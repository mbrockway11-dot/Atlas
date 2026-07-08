# Alpha Hypothesis Generator

Alpha Hypothesis Generator produced 36 candidate rule(s).

## Families

- `momentum`: `9`
- `breadth`: `15`
- `leadership`: `9`
- `topology`: `3`

## Hypotheses

### momentum_top_rank_24_q50

- Family: `momentum`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `asset_with_min_rank_return_24`
- Rank score: `0.5`

Long strongest-ranked asset when 24-period return is above q50 threshold.

Conditions:
- `asset.rank_return_24` <= `1`
- `asset.return_24` > `0.01105646`

### momentum_top_rank_24_q75

- Family: `momentum`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `asset_with_min_rank_return_24`
- Rank score: `0.75`

Long strongest-ranked asset when 24-period return is above q75 threshold.

Conditions:
- `asset.rank_return_24` <= `1`
- `asset.return_24` > `0.16576223`

### momentum_top_rank_24_q90

- Family: `momentum`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `asset_with_min_rank_return_24`
- Rank score: `0.9`

Long strongest-ranked asset when 24-period return is above q90 threshold.

Conditions:
- `asset.rank_return_24` <= `1`
- `asset.return_24` > `0.37735754`

### momentum_top_rank_72_q50

- Family: `momentum`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `asset_with_min_rank_return_72`
- Rank score: `0.5`

Long strongest-ranked asset when 72-period return is above q50 threshold.

Conditions:
- `asset.rank_return_72` <= `1`
- `asset.return_72` > `0.07009224`

### momentum_top_rank_72_q75

- Family: `momentum`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `asset_with_min_rank_return_72`
- Rank score: `0.75`

Long strongest-ranked asset when 72-period return is above q75 threshold.

Conditions:
- `asset.rank_return_72` <= `1`
- `asset.return_72` > `0.39571633`

### momentum_top_rank_72_q90

- Family: `momentum`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `asset_with_min_rank_return_72`
- Rank score: `0.9`

Long strongest-ranked asset when 72-period return is above q90 threshold.

Conditions:
- `asset.rank_return_72` <= `1`
- `asset.return_72` > `0.84247967`

### momentum_top_rank_288_q50

- Family: `momentum`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `asset_with_min_rank_return_288`
- Rank score: `0.5`

Long strongest-ranked asset when 288-period return is above q50 threshold.

Conditions:
- `asset.rank_return_288` <= `1`
- `asset.return_288` > `0.40586234`

### momentum_top_rank_288_q75

- Family: `momentum`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `asset_with_min_rank_return_288`
- Rank score: `0.75`

Long strongest-ranked asset when 288-period return is above q75 threshold.

Conditions:
- `asset.rank_return_288` <= `1`
- `asset.return_288` > `1.40348587`

### momentum_top_rank_288_q90

- Family: `momentum`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `asset_with_min_rank_return_288`
- Rank score: `0.9`

Long strongest-ranked asset when 288-period return is above q90 threshold.

Conditions:
- `asset.rank_return_288` <= `1`
- `asset.return_288` > `6.20529955`

### breadth_positive_24_0_5

- Family: `breadth`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.5`

Long leader when 50%+ of assets are positive over 24.

Conditions:
- `market.breadth_positive_24` >= `0.5`

### breadth_positive_24_0_66

- Family: `breadth`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.66`

Long leader when 66%+ of assets are positive over 24.

Conditions:
- `market.breadth_positive_24` >= `0.66`

### breadth_positive_24_0_8

- Family: `breadth`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.8`

Long leader when 80%+ of assets are positive over 24.

Conditions:
- `market.breadth_positive_24` >= `0.8`

### breadth_positive_24_1_0

- Family: `breadth`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `1.0`

Long leader when 100%+ of assets are positive over 24.

Conditions:
- `market.breadth_positive_24` >= `1.0`

### breadth_dispersion_breakout_24

- Family: `breadth`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.75`

Long leader when cross-sectional spread is elevated over 24.

Conditions:
- `market.spread_return_24` > `0.30776666`
- `market.breadth_positive_24` >= `0.5`

### breadth_positive_72_0_5

- Family: `breadth`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.5`

Long leader when 50%+ of assets are positive over 72.

Conditions:
- `market.breadth_positive_72` >= `0.5`

### breadth_positive_72_0_66

- Family: `breadth`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.66`

Long leader when 66%+ of assets are positive over 72.

Conditions:
- `market.breadth_positive_72` >= `0.66`

### breadth_positive_72_0_8

- Family: `breadth`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.8`

Long leader when 80%+ of assets are positive over 72.

Conditions:
- `market.breadth_positive_72` >= `0.8`

### breadth_positive_72_1_0

- Family: `breadth`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `1.0`

Long leader when 100%+ of assets are positive over 72.

Conditions:
- `market.breadth_positive_72` >= `1.0`

### breadth_dispersion_breakout_72

- Family: `breadth`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.75`

Long leader when cross-sectional spread is elevated over 72.

Conditions:
- `market.spread_return_72` > `0.59725206`
- `market.breadth_positive_72` >= `0.5`

### breadth_positive_288_0_5

- Family: `breadth`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.5`

Long leader when 50%+ of assets are positive over 288.

Conditions:
- `market.breadth_positive_288` >= `0.5`

### breadth_positive_288_0_66

- Family: `breadth`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.66`

Long leader when 66%+ of assets are positive over 288.

Conditions:
- `market.breadth_positive_288` >= `0.66`

### breadth_positive_288_0_8

- Family: `breadth`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.8`

Long leader when 80%+ of assets are positive over 288.

Conditions:
- `market.breadth_positive_288` >= `0.8`

### breadth_positive_288_1_0

- Family: `breadth`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `1.0`

Long leader when 100%+ of assets are positive over 288.

Conditions:
- `market.breadth_positive_288` >= `1.0`

### breadth_dispersion_breakout_288

- Family: `breadth`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.75`

Long leader when cross-sectional spread is elevated over 288.

Conditions:
- `market.spread_return_288` > `4.21572345`
- `market.breadth_positive_288` >= `0.5`

### leader_persistence_24_3

- Family: `leadership`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.7`

Long leader when leadership persists for at least 3 bars over 24.

Conditions:
- `market.leader_persistence_24` >= `3`

### leader_persistence_24_8

- Family: `leadership`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.8`

Long leader when leadership persists for at least 8 bars over 24.

Conditions:
- `market.leader_persistence_24` >= `8`

### leadership_rotation_breakout_24

- Family: `leadership`
- Direction: `LONG`
- Hold period: `24`
- Signal asset rule: `leader_asset_24`
- Rank score: `0.75`

Long new leader after leadership rotation with elevated spread over 24.

Conditions:
- `market.leader_changed_24` == `1`
- `market.leader_laggard_spread_24` > `0.30776666`

### leader_persistence_72_3

- Family: `leadership`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.7`

Long leader when leadership persists for at least 3 bars over 72.

Conditions:
- `market.leader_persistence_72` >= `3`

### leader_persistence_72_8

- Family: `leadership`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.8`

Long leader when leadership persists for at least 8 bars over 72.

Conditions:
- `market.leader_persistence_72` >= `8`

### leadership_rotation_breakout_72

- Family: `leadership`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.75`

Long new leader after leadership rotation with elevated spread over 72.

Conditions:
- `market.leader_changed_72` == `1`
- `market.leader_laggard_spread_72` > `0.59725206`

### leader_persistence_288_3

- Family: `leadership`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.7`

Long leader when leadership persists for at least 3 bars over 288.

Conditions:
- `market.leader_persistence_288` >= `3`

### leader_persistence_288_8

- Family: `leadership`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.8`

Long leader when leadership persists for at least 8 bars over 288.

Conditions:
- `market.leader_persistence_288` >= `8`

### leadership_rotation_breakout_288

- Family: `leadership`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.75`

Long new leader after leadership rotation with elevated spread over 288.

Conditions:
- `market.leader_changed_288` == `1`
- `market.leader_laggard_spread_288` > `4.21572345`

### topology_high_density_leader_72

- Family: `topology`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.7`

Long 72-period leader when correlation graph density is high.

Conditions:
- `market.graph_density` > `1.0`

### topology_low_density_leader_72

- Family: `topology`
- Direction: `LONG`
- Hold period: `72`
- Signal asset rule: `leader_asset_72`
- Rank score: `0.6`

Long 72-period leader when correlation graph density is low.

Conditions:
- `market.graph_density` < `0.66666667`

### topology_high_correlation_leader_288

- Family: `topology`
- Direction: `LONG`
- Hold period: `288`
- Signal asset rule: `leader_asset_288`
- Rank score: `0.65`

Long 288-period leader when average absolute correlation is high.

Conditions:
- `market.avg_abs_corr` > `0.83144717`
