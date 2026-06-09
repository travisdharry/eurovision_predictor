import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict
from simulation_utils import assign_tiers, simulate_year

"""
Monte Carlo Bonus-Only Optimization (Gameplay Version B)
Runs 50 iterations per configuration with randomized strategy assignments
to find optimal bonus values (with penalties disabled) that balance gameplay.
"""

# Set random seed for reproducibility
np.random.seed(42)

# Read the balanced and preprocessed data
df = pd.read_csv('data/song_data_balanced.csv')

print('='*80)
print('GAMEPLAY VERSION B: MONTE CARLO OPTIMIZE BONUSES ONLY')
print('='*80)
print('Players use different strategies (3×tier1, 3×tier2, 2×tier3)')
print('Token bonuses enabled (to be optimized)')
print('Token penalties DISABLED (forced to 0)')
print('This tests if bonuses alone can balance different strategies\n')

# Assign tiers
df = assign_tiers(df, tier1_size=10, tier2_size=10)

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}
PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
STRATEGY_POOL = ['tier1', 'tier1', 'tier1', 'tier2', 'tier2', 'tier2', 'tier3', 'tier3']
NUM_ITERATIONS = 50

def evaluate_bonuses_monte_carlo(bronze_bonus, silver_bonus, gold_bonus):
    """Evaluate a bonus configuration using Monte Carlo simulation."""
    token_values = {
        'Bronze': {'bonus': bronze_bonus, 'penalty': 0},
        'Silver': {'bonus': silver_bonus, 'penalty': 0},
        'Gold': {'bonus': gold_bonus, 'penalty': 0}
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
                penalty_mode='none'  # No penalties, bonuses only
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
        'silver_bonus': silver_bonus,
        'gold_bonus': gold_bonus,
        'std_dev': std_dev,
        'range': score_range,
        'position_means': position_means
    }

print('Searching for optimal bonus values (penalties forced to 0)...')
print(f'Running {NUM_ITERATIONS} iterations per configuration\n')

bronze_bonuses = [3, 5, 7, 10, 15]
silver_bonuses = [25, 50, 75, 100, 150]
gold_bonuses = [150, 250, 350, 500, 750]

configurations = []

print(f'Testing {len(bronze_bonuses) * len(silver_bonuses) * len(gold_bonuses)} configurations...')
print(f'Total simulations: {len(bronze_bonuses) * len(silver_bonuses) * len(gold_bonuses) * NUM_ITERATIONS * 15:,}\n')

count = 0
total = len(bronze_bonuses) * len(silver_bonuses) * len(gold_bonuses)

for bronze_bonus in bronze_bonuses:
    for silver_bonus in silver_bonuses:
        for gold_bonus in gold_bonuses:
            if count % 20 == 0:
                print(f"  Progress: {count}/{total}")
            
            result = evaluate_bonuses_monte_carlo(bronze_bonus, silver_bonus, gold_bonus)
            configurations.append(result)
            count += 1

# Sort by std_dev
configurations.sort(key=lambda x: x['std_dev'])

print(f'\n{"="*80}')
print('TOP 10 MOST BALANCED CONFIGURATIONS (Monte Carlo, Bonuses Only)')
print('='*80)

for i, config in enumerate(configurations[:10], 1):
    print(f'\n#{i}:')
    print(f'  Bronze: +{config["bronze_bonus"]}, Silver: +{config["silver_bonus"]}, Gold: +{config["gold_bonus"]}')
    print(f'  Std Dev: {config["std_dev"]:.1f} points')
    print(f'  Range: {config["range"]:.1f} points')
    scores_str = ', '.join([f'{i+1}:{config["position_means"][i]:.0f}' for i in range(8)])
    print(f'  Position Means: {scores_str}')

# Show best configuration details
best = configurations[0]
print('\n' + '='*80)
print('BEST BONUSES-ONLY CONFIGURATION (Monte Carlo)')
print('='*80)
print(f'Bronze: +{best["bronze_bonus"]} (no penalty)')
print(f'Silver: +{best["silver_bonus"]} (no penalty)')
print(f'Gold: +{best["gold_bonus"]} (no penalty)')
print(f'\nStandard Deviation: {best["std_dev"]:.1f} points')
print(f'Score Range: {best["range"]:.1f} points')

# Save all results to JSON for visualization
os.makedirs('outputs', exist_ok=True)
output_data = {
    'num_iterations': NUM_ITERATIONS,
    'penalty_mode': 'none',
    'configurations': [
        {
            'bronze_bonus': c['bronze_bonus'],
            'silver_bonus': c['silver_bonus'],
            'gold_bonus': c['gold_bonus'],
            'std_dev': c['std_dev'],
            'range': c['range'],
            'position_means': c['position_means']
        }
        for c in configurations
    ]
}

with open('outputs/bonus_optimization_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print('\nResults saved to outputs/bonus_optimization_results.json')
