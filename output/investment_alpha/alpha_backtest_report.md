# Alpha Backtest Report

Alpha Backtesting Engine evaluated 36 hypothesis/hypotheses. Top hypothesis: topology_low_density_leader_72.

- Hypotheses evaluated: `36`
- Minimum trades threshold: `5`

## Top 10

### topology_low_density_leader_72

- Family: `topology`
- Alpha score: `5.893153`
- Raw trades: `633`
- Raw win rate: `0.71406`
- Raw avg return: `0.59543661`
- Raw total return: `2.5801352979763855e+83`
- Raw max drawdown: `-1.0`
- Raw profit factor: `7.172005`
- Non-overlap metrics: `{'trade_count': 224, 'win_rate': 0.714286, 'avg_return': 0.60674584, 'median_return': 0.43690368, 'std_return': 0.96703104, 'min_return': -0.60272562, 'max_return': 4.11704293, 'gross_profit': 157.75035464, 'gross_loss': 21.83928691, 'profit_factor': 7.223237, 'sharpe_like': 9.390536, 'sortino_like': 55.581647, 'final_equity': 4.468510344726137e+29, 'total_return': 4.468510344726137e+29, 'max_drawdown': -0.99999828, 'recovery_factor': 4.468518012997959e+29, 'expectancy': 0.60674584}`
- Asset concentration: `0.663507`

Long 72-period leader when correlation graph density is low.

### leader_persistence_288_8

- Family: `leadership`
- Alpha score: `4.13712`
- Raw trades: `1540`
- Raw win rate: `0.676623`
- Raw avg return: `1.09262675`
- Raw total return: `2.3121589035354367e+120`
- Raw max drawdown: `-1.0`
- Raw profit factor: `7.567673`
- Non-overlap metrics: `{'trade_count': 136, 'win_rate': 0.691176, 'avg_return': 1.23231271, 'median_return': 0.27055276, 'std_return': 3.43449108, 'min_return': -0.8694301, 'max_return': 27.14028379, 'gross_profit': 188.55642199, 'gross_loss': 20.96189373, 'profit_factor': 8.9952, 'sharpe_like': 4.18435, 'sortino_like': 43.370571, 'final_equity': 28584171037146.676, 'total_return': 28584171037145.676, 'max_drawdown': -1.0, 'recovery_factor': 28584171037145.68, 'expectancy': 1.23231271}`
- Asset concentration: `0.570779`

Long leader when leadership persists for at least 8 bars over 288.

### momentum_top_rank_72_q75

- Family: `momentum`
- Alpha score: `4.06169`
- Raw trades: `871`
- Raw win rate: `0.61194`
- Raw avg return: `0.43058575`
- Raw total return: `1.2638086242276396e+83`
- Raw max drawdown: `-1.0`
- Raw profit factor: `5.704975`
- Non-overlap metrics: `{'trade_count': 310, 'win_rate': 0.6, 'avg_return': 0.43469049, 'median_return': 0.21050419, 'std_return': 0.83351854, 'min_return': -0.64978076, 'max_return': 4.11704293, 'gross_profit': 163.75258671, 'gross_loss': 28.99853582, 'profit_factor': 5.646926, 'sharpe_like': 9.182178, 'sortino_like': 45.378387, 'final_equity': 2.348770289088131e+29, 'total_return': 2.348770289088131e+29, 'max_drawdown': -0.99999496, 'recovery_factor': 2.3487821165609603e+29, 'expectancy': 0.43469049}`
- Asset concentration: `0.659013`

Long strongest-ranked asset when 72-period return is above q75 threshold.

### momentum_top_rank_72_q50

- Family: `momentum`
- Alpha score: `3.35111`
- Raw trades: `1344`
- Raw win rate: `0.572917`
- Raw avg return: `0.37929796`
- Raw total return: `1.403457114703245e+98`
- Raw max drawdown: `-1.0`
- Raw profit factor: `4.603339`
- Non-overlap metrics: `{'trade_count': 490, 'win_rate': 0.567347, 'avg_return': 0.37945142, 'median_return': 0.09158115, 'std_return': 0.87535633, 'min_return': -0.69268408, 'max_return': 4.42286952, 'gross_profit': 237.59809614, 'gross_loss': 51.66690207, 'profit_factor': 4.598652, 'sharpe_like': 9.595538, 'sortino_like': 48.498093, 'final_equity': 1.3831465227133227e+35, 'total_return': 1.3831465227133227e+35, 'max_drawdown': -0.99999992, 'recovery_factor': 1.3831466391173848e+35, 'expectancy': 0.37945142}`
- Asset concentration: `0.576637`

Long strongest-ranked asset when 72-period return is above q50 threshold.

### breadth_positive_72_0_66

- Family: `breadth`
- Alpha score: `3.070836`
- Raw trades: `1277`
- Raw win rate: `0.570869`
- Raw avg return: `0.3542796`
- Raw total return: `1.98825870629594e+86`
- Raw max drawdown: `-1.0`
- Raw profit factor: `4.331783`
- Non-overlap metrics: `{'trade_count': 475, 'win_rate': 0.562105, 'avg_return': 0.34891834, 'median_return': 0.0877775, 'std_return': 0.83790327, 'min_return': -0.69268408, 'max_return': 4.11704293, 'gross_profit': 216.97741093, 'gross_loss': 51.24119784, 'profit_factor': 4.234433, 'sharpe_like': 9.075629, 'sortino_like': 43.487504, 'final_equity': 5.364110617558244e+30, 'total_return': 5.364110617558244e+30, 'max_drawdown': -0.99999987, 'recovery_factor': 5.364111296294039e+30, 'expectancy': 0.34891834}`
- Asset concentration: `0.581832`

Long leader when 66%+ of assets are positive over 72.

### breadth_positive_72_0_5

- Family: `breadth`
- Alpha score: `3.061974`
- Raw trades: `1293`
- Raw win rate: `0.573086`
- Raw avg return: `0.35152689`
- Raw total return: `1.2303905022599052e+87`
- Raw max drawdown: `-1.0`
- Raw profit factor: `4.342468`
- Non-overlap metrics: `{'trade_count': 481, 'win_rate': 0.565489, 'avg_return': 0.34682982, 'median_return': 0.0877775, 'std_return': 0.83317842, 'min_return': -0.69268408, 'max_return': 4.11704293, 'gross_profit': 218.14597427, 'gross_loss': 51.32083177, 'profit_factor': 4.250632, 'sharpe_like': 9.129583, 'sortino_like': 43.509334, 'final_equity': 1.3341427257085372e+31, 'total_return': 1.3341427257085372e+31, 'max_drawdown': -0.99999987, 'recovery_factor': 1.334142894521317e+31, 'expectancy': 0.34682982}`
- Asset concentration: `0.574633`

Long leader when 50%+ of assets are positive over 72.

### breadth_dispersion_breakout_24

- Family: `breadth`
- Alpha score: `3.009334`
- Raw trades: `489`
- Raw win rate: `0.619632`
- Raw avg return: `0.29140065`
- Raw total return: `1.1129221029791054e+37`
- Raw max drawdown: `-0.99988643`
- Raw profit factor: `5.519797`
- Non-overlap metrics: `{'trade_count': 489, 'win_rate': 0.619632, 'avg_return': 0.29140065, 'median_return': 0.11056451, 'std_return': 0.56605055, 'min_return': -0.58356319, 'max_return': 3.05772129, 'gross_profit': 174.02176016, 'gross_loss': 31.52683999, 'profit_factor': 5.519797, 'sharpe_like': 11.383865, 'sortino_like': 49.514031, 'final_equity': 1.1129221029791038e+37, 'total_return': 1.1129221029791038e+37, 'max_drawdown': -0.99975049, 'recovery_factor': 1.1131998610382466e+37, 'expectancy': 0.29140065}`
- Asset concentration: `0.672802`

Long leader when cross-sectional spread is elevated over 24.

### breadth_positive_72_0_8

- Family: `breadth`
- Alpha score: `2.856166`
- Raw trades: `963`
- Raw win rate: `0.553479`
- Raw avg return: `0.3381266`
- Raw total return: `9.60365358774588e+58`
- Raw max drawdown: `-1.0`
- Raw profit factor: `4.107201`
- Non-overlap metrics: `{'trade_count': 365, 'win_rate': 0.550685, 'avg_return': 0.33502806, 'median_return': 0.06706516, 'std_return': 0.84337297, 'min_return': -0.68704699, 'max_return': 4.11704293, 'gross_profit': 161.36046294, 'gross_loss': 39.07521931, 'profit_factor': 4.129483, 'sharpe_like': 7.589409, 'sortino_like': 37.073435, 'final_equity': 1.3893139716427649e+22, 'total_return': 1.3893139716427649e+22, 'max_drawdown': -0.9999903, 'recovery_factor': 1.3893274535930314e+22, 'expectancy': 0.33502806}`
- Asset concentration: `0.639668`

Long leader when 80%+ of assets are positive over 72.

### breadth_positive_72_1_0

- Family: `breadth`
- Alpha score: `2.856166`
- Raw trades: `963`
- Raw win rate: `0.553479`
- Raw avg return: `0.3381266`
- Raw total return: `9.60365358774588e+58`
- Raw max drawdown: `-1.0`
- Raw profit factor: `4.107201`
- Non-overlap metrics: `{'trade_count': 365, 'win_rate': 0.550685, 'avg_return': 0.33502806, 'median_return': 0.06706516, 'std_return': 0.84337297, 'min_return': -0.68704699, 'max_return': 4.11704293, 'gross_profit': 161.36046294, 'gross_loss': 39.07521931, 'profit_factor': 4.129483, 'sharpe_like': 7.589409, 'sortino_like': 37.073435, 'final_equity': 1.3893139716427649e+22, 'total_return': 1.3893139716427649e+22, 'max_drawdown': -0.9999903, 'recovery_factor': 1.3893274535930314e+22, 'expectancy': 0.33502806}`
- Asset concentration: `0.639668`

Long leader when 100%+ of assets are positive over 72.

### leader_persistence_288_3

- Family: `leadership`
- Alpha score: `2.847485`
- Raw trades: `1643`
- Raw win rate: `0.686549`
- Raw avg return: `1.20282013`
- Raw total return: `4.297624088753423e+152`
- Raw max drawdown: `-1.0`
- Raw profit factor: `8.629998`
- Non-overlap metrics: `{'trade_count': 147, 'win_rate': 0.707483, 'avg_return': 1.31240653, 'median_return': 0.28879187, 'std_return': 3.86111753, 'min_return': -0.88910251, 'max_return': 33.20009644, 'gross_profit': 214.63130682, 'gross_loss': 21.70754631, 'profit_factor': 9.887405, 'sharpe_like': 4.121108, 'sortino_like': 47.765584, 'final_equity': 3357482092596174.0, 'total_return': 3357482092596173.0, 'max_drawdown': -1.0, 'recovery_factor': 3357482092596173.0, 'expectancy': 1.31240653}`
- Asset concentration: `0.552039`

Long leader when leadership persists for at least 3 bars over 288.
