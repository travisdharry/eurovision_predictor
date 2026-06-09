# Eurovision Fantasy League Balancing
## 15-Minute Technical Presentation Outline

---

## 1. Problem Statement (1.5 minutes)

### Goal
Design a Eurovision fantasy draft game where multiple strategies are viable, not just first-pick optimization.

### Core fairness question
Can we reduce draft-position dominance while keeping the game intuitive?

### Success metrics
- Standard deviation of average player scores across draft positions
- Score range between strongest and weakest positions
- Overlap between strategy outcomes (Tier 1, Tier 2, Tier 3 approaches)

---

## 2. System Architecture (2 minutes)

### Data and processing pipeline
1. `scripts/01_preprocess_data.py`
2. `scripts/02_exploratory_analysis.py`
3. `scripts/03_visualize_exploratory_analysis.py`

### Optimization and evaluation pipeline
4. `scripts/04_optimize_tier_sizes.py`
5. `scripts/05_visualize_tier_optimization.py`
6. `scripts/06_optimize_bonus_values.py`
7. `scripts/07_visualize_bonus_optimization.py`
8. `scripts/08_optimize_bonus_penalty_values.py`
9. `scripts/09_optimize_penalty_modes.py`
10. `scripts/10_visualize_penalty_modes.py`
11. `scripts/11_optimize_gameplay.py`
12. `scripts/12_visualize_gameplay_comparison.py`

### Shared simulation engine
`scripts/simulation_utils.py` centralizes:
- Tier assignment
- Snake draft + rescue draft flow
- Token minting and placement
- Scoring under different penalty modes

---

## 3. Data Engineering Decisions (2 minutes)

### Input data
- Historical Eurovision results with semi/final scores and qualification labels

### Major preprocessing decisions
- Direct qualifiers are split across semi pools for draft fairness
- Missing direct-qualifier semi scores are filled with year-level proxy values
- Output is standardized to `data/song_data_balanced.csv`

### Why this matters
These fixes remove structural bias before gameplay mechanics are tested. Without this, optimization is mostly tuning around data artifacts.

---

## 4. Exploratory Findings (1.5 minutes)

### Tier behavior before game mechanics
- Tier 1 has high consistency and high baseline scoring
- Tier 3 has higher risk but potential high token leverage when qualifiers hit

### Added analysis
Average final score by finishing place helps calibrate expected upside for champion prediction mechanics.

### Deliverables
- `outputs/tier_analysis.txt`
- `outputs/exploratory_analysis.txt`
- `outputs/exploratory_analysis_visualization.png`

---

## 5. Mechanics and Experiments (2.5 minutes)

### Gameplay versions
- Gameplay Version A: baseline draft scoring (control)
- Gameplay Version B: bonus mechanics only
- Gameplay Version C: bonus + penalty system

### Token framework
- Bronze, Silver, Gold tokens minted by qualification from different tiers
- Bonuses reward correct champion prediction
- Penalties tax ownership of predicted countries under selected modes

### Penalty modes tested (isolated A/B/C test)
- `none`
- `winner_only`
- `full`

All three were tested with identical tier sizes and token values to isolate the mode effect.

---

## 6. Optimization Results (2.5 minutes)

### Tier size optimization
- Grid searched tier-size configurations in `scripts/04_optimize_tier_sizes.py`
- Latest 200-iteration run selected Tier 1 = 11, Tier 2 = 12 as most balanced by variance
- Results saved to:
  - `outputs/tier_size_optimization_results.json`
  - `outputs/tier_size_optimization_heatmap.png`

### Penalty-mode optimization (isolated mode comparison)
- Fixed token values across modes
- Result ordering by balance metric:
  1. `full` (best)
  2. `winner_only`
  3. `none`
- Results saved to:
  - `outputs/penalty_mode_optimization_results.json`
  - `outputs/penalty_mode_comparison.png`

### Key design implication
Penalty logic is not a cosmetic rule. It is a primary balancing lever.

---

## 7. Consolidated Gameplay Evaluation (2 minutes)

### Consolidation step
`scripts/11_optimize_gameplay.py` runs Gameplay Versions A/B/C in one Monte Carlo workflow and writes:
- `outputs/gameplay_version_a.json`
- `outputs/gameplay_version_b.json`
- `outputs/gameplay_version_c.json`

### Comparison visualization
`scripts/12_visualize_gameplay_comparison.py` compares:
- Version-level balance metrics (std dev and range)
- Draft-position trajectories
- Strategy distributions

Output:
- `outputs/gameplay_version_comparison.png`

### Product conclusion
Gameplay Version C remains the preferred ruleset for balancing strategy viability while preserving game tension.

---

## 8. Engineering Takeaways (1 minute)

### What worked
- JSON-first architecture (optimizers write; visualizers read)
- Shared utility layer reduced divergence and maintenance overhead
- Isolated A/B testing prevented confounded conclusions

### What this demonstrates
- End-to-end experimentation workflow design
- Reproducible simulation-based balancing
- Data-informed game mechanics design

---

## 9. Closing and Next Steps (0.5 minutes)

### Final answer to the original question
Yes: the project demonstrates a repeatable pipeline that significantly improves fairness and makes multiple draft strategies competitive.

### Next iteration ideas
- Increase Monte Carlo depth for final locked values
- Add sensitivity analysis around token-placement behavior
- Introduce explainability tables for per-year outliers

---

## Optional Appendix Talking Points

### Why tier and penalty tuning must be separate
If tier sizes and penalty rules are tuned together from the start, it becomes hard to identify the true balancing driver. Isolated tests made the `full` penalty impact clear.

### Why archive discipline mattered
Archiving older scripts and outputs reduced ambiguity and ensured all presentation claims map to active scripts only.

### Suggested live demo flow
1. Show script list and workflow order
2. Show exploratory visualization
3. Show tier optimization heatmap
4. Show penalty mode comparison
5. End on gameplay version comparison