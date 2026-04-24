import pandas as pd
import numpy as np
from collections import defaultdict

# Import the simulation logic
np.random.seed(42)
df = pd.read_csv('data/song_data_clustered_semi_normalized.csv')

def get_tier(cluster):
    return 1 if cluster in [2, 3] else (2 if cluster == 1 else 3)

df['tier'] = df['cluster'].apply(get_tier)

# Assign proxy semi scores to direct qualifiers
for year in df['year'].unique():
    year_mask = df['year'] == year
    tier1_mask = (df['tier'] == 1) & year_mask & (df['semi_total_points'].notna())
    if tier1_mask.any():
        median_tier1_score = df.loc[tier1_mask, 'semi_total_points'].median()
        dq_mask = year_mask & (df['semi_total_points'].isna())
        df.loc[dq_mask, 'semi_total_points'] = median_tier1_score

# Copy the simulation code (simplified for speed)
exec(open('fantasy_league_simulation.py').read().split('# Token values')[0])

# Test specific combinations
test_combinations = [
    # (bronze_b, bronze_p, silver_b, silver_p, gold_b, gold_p, description)
    (0, 0, 0, 0, 0, 0, "Baseline (no tokens)"),
    (5, 0, 100, 20, 250, 100, "Your initial guess"),
    (10, 0, 200, 40, 800, 200, "Moderate boost"),
    (10, 0, 300, 40, 1200, 200, "High boost"),
    (20, 0, 300, 40, 1600, 200, "Very high boost"),
    (0, 0, 200, 20, 1000, 150, "Focus on Silver/Gold"),
    (0, 0, 300, 40, 1500, 200, "Maximum Gold value"),
]

print('=== Testing Strategic Token Value Combinations ===\n')

results = []

for bb, bp, sb, sp, gb, gp, desc in test_combinations:
    print(f'Testing: {desc}')
    print(f'  Bronze: +{bb}/-{bp}, Silver: +{sb}/-{sp}, Gold: +{gb}/-{gp}')
    
    # Run simulation with these values
    TOKEN_VALUES = {
        'Bronze': {'bonus': bb, 'penalty': bp},
        'Silver': {'bonus': sb, 'penalty': sp},
        'Gold': {'bonus': gb, 'penalty': gp}
    }
    
    # Simulate all years
    years = sorted(df['year'].unique())
    all_scores = defaultdict(list)
    
    #import the simulate_year function properly
    from fantasy_league_simulation import simulate_year, PLAYER_ORDER
    
    for year in years:
        year_data = df[df['year'] == year]
        try:
            result = simulate_year(year_data, TOKEN_VALUES)
            if result:
                for player in PLAYER_ORDER:
                    all_scores[player].append(result['player_total_scores'][player])
        except:
            pass
    
    # Calculate metrics
    avg_scores = {p: np.mean(all_scores[p]) for p in PLAYER_ORDER}
    std_dev = np.std(list(avg_scores.values()))
    score_range = max(avg_scores.values()) - min(avg_scores.values())
    
    print(f'  Std Dev: {std_dev:.1f}')
    print(f'  Range: {score_range:.1f}')
    
    # Show scores
    sorted_players = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
    score_str = ', '.join([f'{p}:{s:.0f}' for p, s in sorted_players[:4]])
    print(f'  Top 4: {score_str}')
    score_str2 = ', '.join([f'{p}:{s:.0f}' for p, s in sorted_players[4:]])
    print(f'  Bottom 4: {score_str2}')
    print()
    
    results.append({
        'description': desc,
        'bronze': f'+{bb}/-{bp}',
        'silver': f'+{sb}/-{sp}',
        'gold': f'+{gb}/-{gp}',
        'std_dev': std_dev,
        'range': score_range,
        'scores': avg_scores
    })

# Sort by std dev
results.sort(key=lambda x: x['std_dev'])

print('\n=== Summary (sorted by fairness) ===\n')
for i, r in enumerate(results, 1):
    print(f'#{i}: {r["description"]}')
    print(f'    Tokens: Bronze {r["bronze"]}, Silver {r["silver"]}, Gold {r["gold"]}')
    print(f'    Std Dev: {r["std_dev"]:.1f}, Range: {r["range"]:.1f}')
    print()
