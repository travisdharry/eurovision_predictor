import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict
from simulation_utils import assign_tiers, simulate_year

"""
Penalty Mode A/B Test (Isolated Mode Comparison)

Tests three penalty modes with identical tier sizes and token values
to isolate only the effect of penalty mode:
- 'none': No penalties (bonuses only)
- 'winner_only': Penalty only on the champion
- 'full': Penalty on all correct predictions (activated tokens)
"""

# Set random seed for reproducibility
np.random.seed(42)

# Read the balanced and preprocessed data
df = pd.read_csv('data/song_data_balanced.csv')
df = assign_tiers(df, tier1_size=10, tier2_size=10)

print('='*80)
print('PENALTY MODE A/B TEST (ISOLATED MODE CHANGE)')
print('='*80)
print('Testing three penalty modes with identical settings')
print('Players use different strategies (3×tier1, 3×tier2, 2×tier3)')
print('Tier sizes fixed: T1=10, T2=10')
print('Token values fixed for all modes: Bronze +10/-5, Silver +100/-50, Gold +250/-125')
print('Each mode tested with 50 iterations\n')

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}
PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
STRATEGY_POOL = ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3']
NUM_ITERATIONS = 50

# Fixed token values for an isolated mode comparison.
FIXED_TOKEN_VALUES = {
    'Bronze': {'bonus': 10, 'penalty': 5},
    'Silver': {'bonus': 100, 'penalty': 50},
    'Gold': {'bonus': 250, 'penalty': 125}
}

# Test only penalty mode changes (A/B-style isolation)
test_configs = [
    {
        'mode': 'none',
        'token_values': FIXED_TOKEN_VALUES,
        'label': 'A: No Penalties (Control)'
    },
    {
        'mode': 'winner_only',
        'token_values': FIXED_TOKEN_VALUES,
        'label': 'B: Winner-Only Penalty'
    },
    {
        'mode': 'full',
        'token_values': FIXED_TOKEN_VALUES,
        'label': 'C: Full Penalties'
    }
]

def evaluate_penalty_mode(penalty_mode, token_values):
    """Evaluate a penalty mode with given token values using Monte Carlo simulation."""
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
                penalty_mode=penalty_mode
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
        'std_dev': std_dev,
        'range': score_range,
        'position_means': position_means
    }

print(f'Testing {len(test_configs)} configurations...\n')

results = []
for i, config in enumerate(test_configs):
    print(f"Testing {i+1}/{len(test_configs)}: {config['label']}")
    
    result = evaluate_penalty_mode(config['mode'], config['token_values'])
    
    results.append({
        'mode': config['mode'],
        'label': config['label'],
        'token_values': config['token_values'],
        'std_dev': result['std_dev'],
        'range': result['range'],
        'position_means': result['position_means']
    })
    
    print(f"  Std Dev: {result['std_dev']:.1f}, Range: {result['range']:.1f}\n")

# Sort by std_dev
results.sort(key=lambda x: x['std_dev'])

print('='*80)
print('PENALTY MODE A/B TEST RESULTS')
print('='*80)
print(f'Tested {len(test_configs)} configurations with {NUM_ITERATIONS} iterations each\n')

for i, config in enumerate(results, 1):
    print(f'#{i}: {config["label"]}')
    print(f'    Mode: {config["mode"]}')
    print(f'    Std Dev: {config["std_dev"]:.1f} points')
    print(f'    Range: {config["range"]:.1f} points')
    scores_str = ', '.join([f'{i+1}:{config["position_means"][i]:.0f}' for i in range(8)])
    print(f'    Position Means: {scores_str}\n')

# Show best configuration
best = results[0]
print('='*80)
print('BEST PENALTY MODE (ISOLATED TEST)')
print('='*80)
print(f'Mode: {best["mode"]}')
print(f'Label: {best["label"]}')
print(f'Token Values:')
for token, values in best['token_values'].items():
    print(f'  {token}: +{values["bonus"]} / -{values["penalty"]}')
print(f'\nStandard Deviation: {best["std_dev"]:.1f} points')
print(f'Score Range: {best["range"]:.1f} points')

# Save results to JSON
os.makedirs('outputs', exist_ok=True)
output_data = {
    'num_iterations': NUM_ITERATIONS,
    'tier1_size': 10,
    'tier2_size': 10,
    'configurations': results
}

with open('outputs/penalty_mode_optimization_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print('\nResults saved to outputs/penalty_mode_optimization_results.json')
