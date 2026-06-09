import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict
from simulation_utils import assign_tiers, simulate_year

"""
Monte Carlo Tier Size Optimization

Runs 200 iterations per configuration with randomized strategy assignments
to find tier sizes that balance gameplay across all strategy distributions.
"""

# Set random seed for reproducibility
np.random.seed(42)

# Read the balanced and preprocessed data
df = pd.read_csv('data/song_data_balanced.csv')

# Use optimized token values
TOKEN_VALUES = {
    'Bronze': {'bonus': 5, 'penalty': 2},
    'Silver': {'bonus': 50, 'penalty': 25},
    'Gold': {'bonus': 250, 'penalty': 125}
}

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}
PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
STRATEGY_POOL = ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3']
NUM_ITERATIONS = 200

def evaluate_tier_sizes_monte_carlo(tier1_size, tier2_size):
    """Evaluate a tier size configuration using Monte Carlo simulation."""
    df_test = assign_tiers(df, tier1_size, tier2_size)
    
    position_scores = defaultdict(list)
    
    for iteration in range(NUM_ITERATIONS):
        # Randomize strategy assignments
        shuffled_strategies = np.random.permutation(STRATEGY_POOL).tolist()
        players = {
            player: {'strategy': strategy}
            for player, strategy in zip(PLAYER_ORDER, shuffled_strategies)
        }
        
        # Run simulation for all years
        years = sorted(df_test['year'].unique())
        iteration_results = []
        
        for year in years:
            year_data = df_test[df_test['year'] == year]
            result = simulate_year(
                year_data=year_data,
                players=players,
                player_order=PLAYER_ORDER,
                token_values=TOKEN_VALUES,
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
    
    # Calculate tier distribution stats
    tier_counts = df_test.groupby(['year', 'tier']).size().unstack(fill_value=0)
    avg_tier_sizes = tier_counts.mean()
    
    return {
        'tier1_size': tier1_size,
        'tier2_size': tier2_size,
        'std_dev': std_dev,
        'range': score_range,
        'position_means': position_means,
        'avg_tier_sizes': avg_tier_sizes
    }

print("="*80)
print("MONTE CARLO TIER SIZE OPTIMIZATION")
print("="*80)
print(f"Running {NUM_ITERATIONS} iterations per configuration")
print("Testing different Tier 1 and Tier 2 sizes")
print("(Tier 3 gets all remaining countries)\n")

# Test various tier size combinations
test_configs = []
for tier1 in [8, 9, 10, 11, 12]:
    for tier2 in [8, 9, 10, 11, 12]:
        test_configs.append((tier1, tier2))

print(f"Testing {len(test_configs)} configurations...")
print(f"Total simulations: {len(test_configs) * NUM_ITERATIONS * 15} = {len(test_configs) * NUM_ITERATIONS * 15:,}\n")

results = []
for i, (tier1, tier2) in enumerate(test_configs):
    if i % 5 == 0:
        print(f"  Progress: {i}/{len(test_configs)}")
    
    result = evaluate_tier_sizes_monte_carlo(tier1, tier2)
    results.append(result)

# Sort by std_dev (lower is better)
results.sort(key=lambda x: x['std_dev'])

print(f"\n{'='*80}")
print("TOP 10 MOST BALANCED TIER SIZE CONFIGURATIONS (Monte Carlo)")
print(f"{'='*80}\n")

for i, config in enumerate(results[:10], 1):
    print(f"#{i}: Tier 1={config['tier1_size']}, Tier 2={config['tier2_size']}")
    print(f"    Std Dev = {config['std_dev']:.1f}, Range = {config['range']:.1f}")
    tier_sizes_str = ', '.join([f'T{j+1}={config["avg_tier_sizes"][j+1]:.1f}' for j in range(3)])
    print(f"    Average tier sizes per year: {tier_sizes_str}")
    scores_str = ', '.join([f'{i+1}:{config["position_means"][i]:.0f}' for i in range(8)])
    print(f"    Position means: {scores_str}\n")

# Show best configuration
best = results[0]
print('='*80)
print('BEST TIER SIZE CONFIGURATION (Monte Carlo)')
print('='*80)
print(f'Tier 1 Size: {best["tier1_size"]}')
print(f'Tier 2 Size: {best["tier2_size"]}')
print(f'\nStandard Deviation: {best["std_dev"]:.1f} points')
print(f'Score Range: {best["range"]:.1f} points')

# Save all results to JSON for visualization
os.makedirs('outputs', exist_ok=True)
output_data = {
    'num_iterations': NUM_ITERATIONS,
    'token_values': TOKEN_VALUES,
    'configurations': [
        {
            'tier1_size': r['tier1_size'],
            'tier2_size': r['tier2_size'],
            'std_dev': r['std_dev'],
            'range': r['range'],
            'position_means': r['position_means']
        }
        for r in results
    ]
}

with open('outputs/tier_size_optimization_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print('\nResults saved to outputs/tier_size_optimization_results.json')
