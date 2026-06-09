import pandas as pd
import numpy as np
import json
from collections import defaultdict
from simulation_utils import assign_tiers, simulate_year

"""
Comprehensive Bonus AND Penalty Value Optimization (Monte Carlo)

Tests combinations of bonus AND penalty values together to find optimal
token configurations. Uses penalty_mode='full' throughout.

Runs 50 iterations per configuration with randomized strategy assignments
to find token values that balance gameplay across all strategy distributions.

Tests 81 configurations:
- Bronze bonuses: 5, 10, 15
- Silver bonuses: 50, 100, 150
- Gold bonuses: 150, 200, 250
- Penalty ratios: 0%, 20%, 50% of bonus value
"""

# Set random seed for reproducibility
np.random.seed(42)

# Read the balanced and preprocessed data
df = pd.read_csv('data/song_data_balanced.csv')

# Assign tiers
df = assign_tiers(df, tier1_size=10, tier2_size=10)

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}
PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
STRATEGY_POOL = ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3']
NUM_ITERATIONS = 50

def evaluate_token_values_monte_carlo(bronze_bonus, bronze_penalty, silver_bonus, silver_penalty, gold_bonus, gold_penalty):
    """Evaluate a token configuration using Monte Carlo simulation."""
    token_values = {
        'Bronze': {'bonus': bronze_bonus, 'penalty': bronze_penalty},
        'Silver': {'bonus': silver_bonus, 'penalty': silver_penalty},
        'Gold': {'bonus': gold_bonus, 'penalty': gold_penalty}
    }
    
    position_scores = defaultdict(list)
    
    for iteration in range(NUM_ITERATIONS):
        # Randomize strategy assignments
        shuffled_strategies = np.random.permutation(STRATEGY_POOL).tolist()
        players = {
            player: {'strategy': strategy}
            for player, strategy in zip(PLAYER_ORDER, shuffled_strategies)
        }
        
        # Run simulation for all years
        years = sorted(df['year'].unique())
        iteration_results = []
        
        for year in years:
            year_data = df[df['year'] == year]
            result = simulate_year(
                year_data=year_data,
                players=players,
                player_order=PLAYER_ORDER,
                token_values=token_values,
                tier_to_token=TIER_TO_TOKEN,
                penalty_mode='full'
            )
            if result is not None:
                iteration_results.append(result)
        
        # Calculate total scores for this iteration
        iteration_total_scores = defaultdict(list)
        for result in iteration_results:
            for player in PLAYER_ORDER:
                iteration_total_scores[player].append(result['player_total_scores'][player])
        
        # Store average score by position
        for i, player in enumerate(PLAYER_ORDER):
            avg_score = np.mean(iteration_total_scores[player])
            position_scores[i].append(avg_score)
    
    # Calculate position means across all iterations
    position_means = [np.mean(position_scores[i]) for i in range(8)]
    std_dev = np.std(position_means)
    score_range = max(position_means) - min(position_means)
    
    return {
        'bronze_bonus': bronze_bonus,
        'bronze_penalty': bronze_penalty,
        'silver_bonus': silver_bonus,
        'silver_penalty': silver_penalty,
        'gold_bonus': gold_bonus,
        'gold_penalty': gold_penalty,
        'std_dev': std_dev,
        'range': score_range,
        'position_means': position_means
    }

print("="*80)
print("MONTE CARLO TOKEN VALUE OPTIMIZATION")
print("="*80)
print(f"Running {NUM_ITERATIONS} iterations per configuration")
print("Goal: Minimize score variance across randomized strategies\n")

# Test a range of values focusing on reasonable scales
test_configs = []

for bronze_b in [5, 10, 15]:
    for silver_b in [50, 100, 150]:
        for gold_b in [150, 200, 250]:
            for penalty_ratio in [0.0, 0.2, 0.5]:
                test_configs.append({
                    'bronze_bonus': bronze_b,
                    'bronze_penalty': int(bronze_b * penalty_ratio),
                    'silver_bonus': silver_b,
                    'silver_penalty': int(silver_b * penalty_ratio),
                    'gold_bonus': gold_b,
                    'gold_penalty': int(gold_b * penalty_ratio)
                })

print(f"Testing {len(test_configs)} configurations...")
print(f"Total simulations: {len(test_configs) * NUM_ITERATIONS * 15} = {len(test_configs) * NUM_ITERATIONS * 15:,}\n")

results = []
for i, config in enumerate(test_configs):
    if i % 10 == 0:
        print(f"  Progress: {i}/{len(test_configs)}")
    
    result = evaluate_token_values_monte_carlo(**config)
    results.append(result)

# Sort by std_dev (lower is better)
results.sort(key=lambda x: x['std_dev'])

print(f"\n{'='*80}")
print("TOP 10 MOST BALANCED TOKEN VALUE COMBINATIONS (Monte Carlo)")
print(f"{'='*80}\n")

for i, config in enumerate(results[:10], 1):
    print(f"#{i}:")
    print(f"  Bronze: +{config['bronze_bonus']}/-{config['bronze_penalty']}, "
          f"Silver: +{config['silver_bonus']}/-{config['silver_penalty']}, "
          f"Gold: +{config['gold_bonus']}/-{config['gold_penalty']}")
    print(f"  Std Dev: {config['std_dev']:.1f} points")
    print(f"  Range: {config['range']:.1f} points")
    scores_str = ', '.join([f'{i+1}:{config["position_means"][i]:.0f}' for i in range(8)])
    print(f"  Position Means: {scores_str}\n")

# Show best configuration
best = results[0]
print('='*80)
print('BEST CONFIGURATION (Monte Carlo)')
print('='*80)
print(f'Bronze: +{best["bronze_bonus"]}/-{best["bronze_penalty"]}')
print(f'Silver: +{best["silver_bonus"]}/-{best["silver_penalty"]}')
print(f'Gold: +{best["gold_bonus"]}/-{best["gold_penalty"]}')
print(f'\nStandard Deviation: {best["std_dev"]:.1f} points')
print(f'Score Range: {best["range"]:.1f} points')

import json
output_data = {
    'configurations': results,
    'best_config': best,
    'num_iterations': NUM_ITERATIONS,
    'num_configs_tested': len(test_configs)
}

with open('outputs/bonus_penalty_optimization_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f'\nResults saved to outputs/bonus_penalty_optimization_results.json')
