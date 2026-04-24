import pandas as pd
import numpy as np
from itertools import product

# Read the clustered data with direct qualifiers as cluster 3
df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Get all years that have both semi-finals
years_with_semis = df[df['semi_final'].astype(str).isin(['1', '2'])]['year'].unique()
years_with_semis = sorted([y for y in years_with_semis if y >= 2009])  # Modern era

print(f'=== Token Value Optimization for Fair Fantasy Draft ===')
print(f'Testing different token values to minimize score variance\n')
print(f'All players use safe strategy (pick highest tier available)\n')

# Define search space
gold_values = [0, 100, 200, 300, 400, 500, 600, 700, 800]
silver_values = [0, 50, 100, 150, 200, 250, 300, 350, 400]
bronze_values = [0, 25, 50, 75, 100, 125, 150]

print(f'Search space: {len(gold_values)} gold × {len(silver_values)} silver × {len(bronze_values)} bronze = {len(gold_values) * len(silver_values) * len(bronze_values)} combinations\n')

def simulate_draft_with_tokens(gold_value, silver_value, bronze_value):
    """Run draft simulation and return standard deviation of total points"""
    all_results = []
    
    for YEAR in years_with_semis:
        year_data = df[df['year'] == YEAR].copy()
        
        # Split by semi-final
        semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
        semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
        
        # Skip if not enough entries
        if len(semi1) < 15 or len(semi2) < 16:
            continue
        
        # Simulate draft
        semi1_draft_order = [1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1]
        semi2_draft_order = [8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]
        
        # Initialize player rosters and tokens
        player_rosters = {i: [] for i in range(1, 9)}
        player_tokens = {i: {'gold': 0, 'silver': 0, 'bronze': 0} for i in range(1, 9)}
        
        def pick_country(available_pool):
            """Pick best country - all players use safe strategy"""
            return available_pool.sort_values(['cluster', 'semi_total_points'], 
                                             ascending=[False, False]).iloc[0]
        
        # Semi 1 draft
        semi1_available = semi1.copy()
        for player in semi1_draft_order:
            if len(semi1_available) > 0:
                country = pick_country(semi1_available)
                player_rosters[player].append(country)
                
                # Award tokens
                cluster = country['cluster']
                qualified = country['qualified_10'] == 1
                
                if cluster == 0 and qualified:
                    player_tokens[player]['gold'] += 1
                elif cluster == 1 and qualified:
                    player_tokens[player]['silver'] += 1
                elif cluster == 2:  # All Tier 2 get bronze (they all qualify)
                    player_tokens[player]['bronze'] += 1
                
                # Remove picked country from available pool
                semi1_available = semi1_available[semi1_available.index != country.name]
        
        # Semi 2 draft
        semi2_available = semi2.copy()
        for player in semi2_draft_order:
            if len(semi2_available) > 0:
                country = pick_country(semi2_available)
                player_rosters[player].append(country)
                
                # Award tokens
                cluster = country['cluster']
                qualified = country['qualified_10'] == 1
                
                if cluster == 0 and qualified:
                    player_tokens[player]['gold'] += 1
                elif cluster == 1 and qualified:
                    player_tokens[player]['silver'] += 1
                elif cluster == 2:  # All Tier 2 get bronze (they all qualify)
                    player_tokens[player]['bronze'] += 1
                
                # Remove picked country from available pool
                semi2_available = semi2_available[semi2_available.index != country.name]
        
        # Calculate total points and tokens for each player
        for player in range(1, 9):
            roster = player_rosters[player]
            actual_points = sum(country['final_total_points'] for country in roster)
            
            # Calculate token points with provided values
            token_points = (player_tokens[player]['gold'] * gold_value + 
                          player_tokens[player]['silver'] * silver_value + 
                          player_tokens[player]['bronze'] * bronze_value)
            
            all_results.append({
                'year': YEAR,
                'player': player,
                'actual_points': actual_points,
                'token_points': token_points,
                'total_points': actual_points + token_points
            })
    
    # Calculate standard deviation across players
    results_df = pd.DataFrame(all_results)
    player_avg = results_df.groupby('player')['total_points'].mean()
    std_dev = player_avg.std()
    min_score = player_avg.min()
    max_score = player_avg.max()
    score_range = max_score - min_score
    
    return std_dev, score_range, player_avg.to_dict()

# Run grid search
best_results = []

print('Running optimization... (this may take a minute)\n')

for gold, silver, bronze in product(gold_values, silver_values, bronze_values):
    std_dev, score_range, player_scores = simulate_draft_with_tokens(gold, silver, bronze)
    
    best_results.append({
        'gold': gold,
        'silver': silver,
        'bronze': bronze,
        'std_dev': std_dev,
        'score_range': score_range,
        'player_scores': player_scores
    })

# Convert to DataFrame and sort by standard deviation
results_df = pd.DataFrame(best_results)
results_df = results_df.sort_values('std_dev')

print('=== Top 15 Most Fair Token Value Combinations ===')
print('(Sorted by standard deviation - lower is more fair)\n')

for i, row in results_df.head(15).iterrows():
    print(f'#{results_df.index.get_loc(i) + 1}:')
    print(f'  Gold={row["gold"]}, Silver={row["silver"]}, Bronze={row["bronze"]}')
    print(f'  Std Dev: {row["std_dev"]:.1f} points')
    print(f'  Range: {row["score_range"]:.1f} points (max-min)')
    
    # Show player scores for this combination
    scores = row['player_scores']
    sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    score_str = ', '.join([f'P{p}:{s:.0f}' for p, s in sorted_players])
    print(f'  Scores: {score_str}')
    print()

print('\n=== Analysis ===')

# Show baseline (no tokens)
baseline = results_df[results_df['gold'] == 0].iloc[0]
print(f'Baseline (no tokens):')
print(f'  Std Dev: {baseline["std_dev"]:.1f}')
print(f'  Range: {baseline["score_range"]:.1f}')

# Show best
best = results_df.iloc[0]
print(f'\nOptimal token values:')
print(f'  Gold={best["gold"]}, Silver={best["silver"]}, Bronze={best["bronze"]}')
print(f'  Std Dev: {best["std_dev"]:.1f} ({((best["std_dev"] - baseline["std_dev"]) / baseline["std_dev"] * 100):.1f}% change)')
print(f'  Range: {best["score_range"]:.1f} ({((best["score_range"] - baseline["score_range"]) / baseline["score_range"] * 100):.1f}% change)')

# Show current system (200/100/50)
current = results_df[(results_df['gold'] == 200) & (results_df['silver'] == 100) & (results_df['bronze'] == 50)]
if len(current) > 0:
    current = current.iloc[0]
    rank = results_df.index.get_loc(current.name) + 1
    print(f'\nCurrent system (200/100/50):')
    print(f'  Rank: #{rank} out of {len(results_df)}')
    print(f'  Std Dev: {current["std_dev"]:.1f}')
    print(f'  Range: {current["score_range"]:.1f}')
