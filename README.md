# Eurovision Predictor

A data-driven Eurovision fantasy league simulator and balance-testing toolkit. The project uses historical Eurovision results to test draft strategies, token mechanics, tier structures, and penalty modes with Monte Carlo simulation.

## What This Project Does

The current workflow models an 8-player fantasy game with:
- a snake draft across the Eurovision semi-finals
- tier-based country assignment by year
- token bonuses and penalties tied to qualification outcomes
- three gameplay versions for comparison
- statistical optimization of tier sizes, token values, and penalty behavior


## Data Flow

```text
song_data.csv
  -> song_data_manual_preprocessing.csv
  -> song_data_balanced.csv
  -> simulation / optimization / visualization scripts
```

## Current Script Workflow

The scripts are numbered in the order the project is intended to run.

### 01. Preprocess Data

[01_preprocess_data.py](scripts/01_preprocess_data.py)

Prepares the balanced dataset used everywhere else.
- assigns direct qualifiers into the semi-final pools
- creates [data/song_data_balanced.csv](data/song_data_balanced.csv)

### 02. Exploratory Analysis

[02_exploratory_analysis.py](scripts/02_exploratory_analysis.py)

Generates tier diagnostics and writes [outputs/tier_analysis.txt](outputs/tier_analysis.txt).
- qualification rate by tier
- average final score by tier
- average final score for qualifiers by finishing place

### 03. Exploratory Visualization

[03_visualize_exploratory_analysis.py](scripts/03_visualize_exploratory_analysis.py)

Creates [outputs/exploratory_analysis_visualization.png](outputs/exploratory_analysis_visualization.png).
- scatter plot: overall qualification rate vs average final score for qualifiers
- bar chart: average final score for qualifiers by finishing place

### 04. Tier Size Optimization

[04_optimize_tier_sizes.py](scripts/04_optimize_tier_sizes.py)

Tests tier-size combinations with Monte Carlo simulation.
- current search grid: Tier 1 = 8 to 12, Tier 2 = 8 to 12
- current best result from the latest 200-iteration run: T1=11, T2=12
- writes [outputs/tier_size_optimization_results.json](outputs/tier_size_optimization_results.json)

### 05. Tier Size Visualization

[05_visualize_tier_optimization.py](scripts/05_visualize_tier_optimization.py)

Reads the tier-size results JSON and generates [outputs/tier_size_optimization_heatmap.png](outputs/tier_size_optimization_heatmap.png).

### 06. Bonus-Only Optimization

[06_optimize_bonus_values.py](scripts/06_optimize_bonus_values.py)

Searches bonus values while keeping penalties at zero.
- used to isolate the effect of bonuses only
- writes [outputs/bonus_optimization_results.json](outputs/bonus_optimization_results.json)

### 07. Bonus Visualization

[07_visualize_bonus_optimization.py](scripts/07_visualize_bonus_optimization.py)

Generates [outputs/bonus_optimization_heatmap.png](outputs/bonus_optimization_heatmap.png).

### 08. Bonus + Penalty Optimization

[08_optimize_bonus_penalty_values.py](scripts/08_optimize_bonus_penalty_values.py)

Searches bonus and penalty values together.
- used to evaluate combined token values
- writes [outputs/bonus_penalty_optimization_results.json](outputs/bonus_penalty_optimization_results.json)

### 09. Penalty-Mode Optimization

[09_optimize_penalty_modes.py](scripts/09_optimize_penalty_modes.py)

Isolates penalty mode as the only variable.
- fixed tier sizes: T1=10, T2=10
- fixed token values: Bronze +10/-5, Silver +100/-50, Gold +250/-125
- compares `none`, `winner_only`, and `full`
- writes [outputs/penalty_mode_optimization_results.json](outputs/penalty_mode_optimization_results.json)

### 10. Penalty Visualization

[10_visualize_penalty_modes.py](scripts/10_visualize_penalty_modes.py)

Creates [outputs/penalty_mode_comparison.png](outputs/penalty_mode_comparison.png).

### 11. Gameplay Optimization

[11_optimize_gameplay.py](scripts/11_optimize_gameplay.py)

Runs the three gameplay versions in a single Monte Carlo pass and writes:
- [outputs/gameplay_version_a.json](outputs/gameplay_version_a.json)
- [outputs/gameplay_version_b.json](outputs/gameplay_version_b.json)
- [outputs/gameplay_version_c.json](outputs/gameplay_version_c.json)

Current gameplay setup:
- fixed tier sizes: T1=10, T2=10
- Version A: no mechanics, all players tier 1 strategy
- Version B: bonuses only
- Version C: full bonus + penalty system

### 12. Gameplay Comparison Visualization

[12_visualize_gameplay_comparison.py](scripts/12_visualize_gameplay_comparison.py)

Creates [outputs/gameplay_version_comparison.png](outputs/gameplay_version_comparison.png).



## Project Structure

```text
eurovision_predictor/
├── README.md
├── data/
├── outputs/
│   ├── archive/
│   └── ...generated results...
└── scripts/
    ├── 01_preprocess_data.py
    ├── 02_exploratory_analysis.py
    ├── 03_visualize_exploratory_analysis.py
    ├── 04_optimize_tier_sizes.py
    ├── 05_visualize_tier_optimization.py
    ├── 06_optimize_bonus_values.py
    ├── 07_visualize_bonus_optimization.py
    ├── 08_optimize_bonus_penalty_values.py
    ├── 09_optimize_penalty_modes.py
    ├── 10_visualize_penalty_modes.py
    ├── 11_optimize_gameplay.py
    ├── 12_visualize_gameplay_comparison.py
    └── simulation_utils.py
```

## Notes

- The project uses Python, pandas, numpy, matplotlib, and seaborn.
- Monte Carlo runs are used to reduce sensitivity to draft-order luck.

## Quick Start

```bash
# 1. Build the balanced dataset
python scripts/01_preprocess_data.py

# 2. Run exploratory analysis and visualization
python scripts/02_exploratory_analysis.py
python scripts/03_visualize_exploratory_analysis.py

# 3. Run optimization passes
python scripts/04_optimize_tier_sizes.py
python scripts/05_visualize_tier_optimization.py
python scripts/06_optimize_bonus_values.py
python scripts/07_visualize_bonus_optimization.py
python scripts/08_optimize_bonus_penalty_values.py
python scripts/09_optimize_penalty_modes.py
python scripts/10_visualize_penalty_modes.py

# 4. Run gameplay comparison
python scripts/11_optimize_gameplay.py
python scripts/12_visualize_gameplay_comparison.py
```
