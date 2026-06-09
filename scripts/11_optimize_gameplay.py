import json
from collections import defaultdict

import numpy as np
import pandas as pd

from simulation_utils import assign_tiers, simulate_year

"""
Consolidated Gameplay Optimization (Monte Carlo)

Runs Gameplay Versions A, B, and C in a single script and writes:
- outputs/gameplay_version_a.json
- outputs/gameplay_version_b.json
- outputs/gameplay_version_c.json

This replaces running scripts 07/08/09 separately.
"""

PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}
NUM_ITERATIONS = 100


def run_gameplay_version(df, config):
    """Run one gameplay version and return aggregate Monte Carlo metrics."""
    # Re-seed per version to keep deterministic behavior aligned with old per-script runs.
    np.random.seed(42)

    position_scores = defaultdict(list)
    strategy_scores = defaultdict(list)

    print('=' * 80)
    print(config['header'])
    print('=' * 80)
    print(f"Running {NUM_ITERATIONS} iterations")
    print(config['details'])
    print('')

    years = sorted(df['year'].unique())

    for iteration in range(NUM_ITERATIONS):
        if (iteration + 1) % 20 == 0:
            print(f"  Iteration {iteration + 1}/{NUM_ITERATIONS}...")

        shuffled_strategies = np.random.permutation(config['strategy_pool']).tolist()
        players = {
            player: {'strategy': strategy}
            for player, strategy in zip(PLAYER_ORDER, shuffled_strategies)
        }

        iteration_results = []
        for year in years:
            year_data = df[df['year'] == year]
            result = simulate_year(
                year_data=year_data,
                players=players,
                player_order=PLAYER_ORDER,
                token_values=config['token_values'],
                tier_to_token=TIER_TO_TOKEN,
                penalty_mode=config['penalty_mode'],
            )
            if result is not None:
                iteration_results.append(result)

        iteration_total_scores = defaultdict(list)
        for result in iteration_results:
            for player in PLAYER_ORDER:
                iteration_total_scores[player].append(result['player_total_scores'][player])

        for i, player in enumerate(PLAYER_ORDER):
            avg_score = np.mean(iteration_total_scores[player])
            position_scores[i].append(avg_score)
            strategy_scores[players[player]['strategy']].append(avg_score)

    print(f"\nCompleted {NUM_ITERATIONS} iterations\n")

    print('=' * 80)
    print(config['results_header'])
    print('=' * 80)

    position_means = []
    for i in range(8):
        mean_score = np.mean(position_scores[i])
        position_means.append(mean_score)
        print(f"Position {i + 1}: {mean_score:.1f} points")

    std_dev = np.std(position_means)
    score_range = max(position_means) - min(position_means)

    print(f"\nStandard Deviation: {std_dev:.1f} points")
    print(f"Range: {score_range:.1f} points")

    output = {
        'version': config['version_label'],
        'position_means': position_means,
        'std_dev': std_dev,
        'range': score_range,
        'strategy_scores': {k: list(v) for k, v in strategy_scores.items()},
    }

    with open(config['output_path'], 'w') as f:
        json.dump(output, f)

    print(f"\nResults saved to {config['output_path']}\n")


def main():
    df = pd.read_csv('data/song_data_balanced.csv')
    df = assign_tiers(df, tier1_size=10, tier2_size=10)

    gameplay_configs = [
        {
            'key': 'a',
            'header': 'GAMEPLAY VERSION A (MONTE CARLO): BASELINE - NO MECHANICS',
            'details': 'All players: Tier 1 strategy\nBonuses: OFF, Penalties: OFF',
            'results_header': 'GAMEPLAY VERSION A RESULTS: Draft Position Performance',
            'version_label': 'Gameplay Version A: Baseline',
            'penalty_mode': 'none',
            'strategy_pool': ['tier1'] * 8,
            'token_values': {
                'Bronze': {'bonus': 0, 'penalty': 0},
                'Silver': {'bonus': 0, 'penalty': 0},
                'Gold': {'bonus': 0, 'penalty': 0},
            },
            'output_path': 'outputs/gameplay_version_a.json',
        },
        {
            'key': 'b',
            'header': 'GAMEPLAY VERSION B (MONTE CARLO): BONUSES ONLY',
            'details': 'Strategy Pool: 3xTier1, 3xTier2, 2xTier3\nBonuses: OPTIMIZED, Penalties: OFF',
            'results_header': 'GAMEPLAY VERSION B RESULTS: Draft Position Performance',
            'version_label': 'Gameplay Version B: Bonuses Only',
            'penalty_mode': 'none',
            'strategy_pool': ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3'],
            'token_values': {
                'Bronze': {'bonus': 10, 'penalty': 0},
                'Silver': {'bonus': 150, 'penalty': 0},
                'Gold': {'bonus': 350, 'penalty': 0},
            },
            'output_path': 'outputs/gameplay_version_b.json',
        },
        {
            'key': 'c',
            'header': 'GAMEPLAY VERSION C (MONTE CARLO): FULL SYSTEM',
            'details': 'Strategy Pool: 3xTier1, 3xTier2, 2xTier3\nBonuses: OPTIMIZED, Penalties: OPTIMIZED',
            'results_header': 'GAMEPLAY VERSION C RESULTS: Draft Position Performance',
            'version_label': 'Gameplay Version C: Full System',
            'penalty_mode': 'full',
            'strategy_pool': ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3'],
            'token_values': {
                'Bronze': {'bonus': 5, 'penalty': 2},
                'Silver': {'bonus': 50, 'penalty': 25},
                'Gold': {'bonus': 250, 'penalty': 125},
            },
            'output_path': 'outputs/gameplay_version_c.json',
        },
    ]

    for config in gameplay_configs:
        run_gameplay_version(df, config)


if __name__ == '__main__':
    main()
