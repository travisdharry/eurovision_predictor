import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import product

# Set random seed for reproducibility
np.random.seed(42)

# Read the normalized clustering data
df = pd.read_csv('data/song_data_clustered_semi_normalized.csv')

# Map clusters to tiers
def get_tier(cluster):
    if cluster in [2, 3]:
        return 1
    elif cluster == 1:
        return 2
    else:  # cluster 0
        return 3

df['tier'] = df['cluster'].apply(get_tier)

# Assign proxy semi scores to direct qualifiers
for year in df['year'].unique():
    year_mask = df['year'] == year
    tier1_mask = (df['tier'] == 1) & year_mask & (df['semi_total_points'].notna())
    
    if tier1_mask.any():
        median_tier1_score = df.loc[tier1_mask, 'semi_total_points'].median()
        dq_mask = year_mask & (df['semi_total_points'].isna())
        df.loc[dq_mask, 'semi_total_points'] = median_tier1_score

# Player strategies
PLAYERS = {
    'A': {'strategy': 'tier1'}, 'B': {'strategy': 'tier1'}, 'C': {'strategy': 'tier1'},
    'D': {'strategy': 'tier2'}, 'E': {'strategy': 'tier2'}, 'F': {'strategy': 'tier2'},
    'G': {'strategy': 'tier3'}, 'H': {'strategy': 'tier3'}
}

PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}

def pick_country(available_pool, strategy):
    """Pick best country from pool based on strategy and semi scores"""
    if len(available_pool) == 0:
        return None
    
    preferred_tier = 1 if strategy == 'tier1' else (2 if strategy == 'tier2' else 3)
    preferred = available_pool[available_pool['tier'] == preferred_tier]
    
    if len(preferred) > 0:
        return preferred.nlargest(1, 'semi_total_points', keep='first').iloc[0]
    return available_pool.nlargest(1, 'semi_total_points', keep='first').iloc[0]

def simulate_year(year_data, token_values):
    """Simulate one year with given token values"""
    
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    direct_qual = year_data[year_data['semi_final'].astype(str) == '-'].copy()
    
    if len(semi1) < 8 or len(semi2) < 8:
        return None
    
    player_countries = {p: [] for p in PLAYER_ORDER}
    player_tokens = {p: {'Bronze': 0, 'Silver': 0, 'Gold': 0} for p in PLAYER_ORDER}
    drafted_countries = []
    
    # DRAFT 1
    draft1_order = PLAYER_ORDER + PLAYER_ORDER[::-1]
    draft1_pool = pd.concat([semi1, direct_qual]).copy()
    
    for player in draft1_order:
        available = draft1_pool[~draft1_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI 1: Mint tokens
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            if country_row['semi_final'] == '1' and country_row['qualified_10'] == 1:
                token_type = TIER_TO_TOKEN[country_row['tier']]
                player_tokens[player][token_type] += 1
            elif country_row['semi_final'] == '-':
                player_tokens[player]['Bronze'] += 1
    
    # DRAFT 2
    draft2_order = PLAYER_ORDER[::-1] + PLAYER_ORDER
    draft2_pool = semi2.copy()
    
    for player in draft2_order:
        available = draft2_pool[~draft2_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI 2: Mint tokens
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            if country_row['semi_final'] == '2' and country_row['qualified_10'] == 1:
                token_type = TIER_TO_TOKEN[country_row['tier']]
                player_tokens[player][token_type] += 1
    
    # Count qualifiers
    player_qualifiers = {}
    for player in PLAYER_ORDER:
        qualifiers = [c for c in player_countries[player] 
                     if c['qualified_10'] == 1 or c['semi_final'] == '-']
        player_qualifiers[player] = qualifiers
    
    # RESCUE DRAFT
    all_qualifiers = year_data[
        (year_data['qualified_10'] == 1) | (year_data['semi_final'].astype(str) == '-')
    ].copy()
    
    for player in PLAYER_ORDER:
        while len(player_qualifiers[player]) < 3:
            available_rescue = all_qualifiers[~all_qualifiers['country'].isin(drafted_countries)]
            if len(available_rescue) == 0:
                break
            rescue_pick = available_rescue.nlargest(1, 'semi_total_points', keep='first').iloc[0]
            player_countries[player].append(rescue_pick)
            player_qualifiers[player].append(rescue_pick)
            drafted_countries.append(rescue_pick['country'])
    
    # FINAL ROSTER
    player_final_roster = {}
    for player in PLAYER_ORDER:
        if len(player_qualifiers[player]) >= 3:
            sorted_qual = sorted(player_qualifiers[player], 
                               key=lambda x: x['final_total_points'], reverse=True)
            player_final_roster[player] = sorted_qual[:3]
        else:
            player_final_roster[player] = player_qualifiers[player]
    
    # BASE SCORES
    player_base_scores = {}
    for player in PLAYER_ORDER:
        player_base_scores[player] = sum(c['final_total_points'] for c in player_final_roster[player])
    
    # Find champion
    champion_row = year_data[year_data['is_champion'] == 1].iloc[0]
    champion_country = champion_row['country']
    champion_owner = None
    
    for player in PLAYER_ORDER:
        roster_countries = [c['country'] for c in player_final_roster[player]]
        if champion_country in roster_countries:
            champion_owner = player
            break
    
    # TOKEN PLACEMENT
    player_token_placements = {p: [] for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        tokens_to_place = []
        for token_type, count in player_tokens[player].items():
            tokens_to_place.extend([token_type] * count)
        
        if len(tokens_to_place) > 0 and len(player_final_roster[player]) > 0:
            roster_scores = [(c['country'], c['final_total_points']) for c in player_final_roster[player]]
            weights = [0.7, 0.2, 0.1][:len(roster_scores)]
            weights = np.array(weights) / sum(weights)
            
            for token in tokens_to_place:
                placed_country = np.random.choice([c[0] for c in roster_scores], p=weights)
                player_token_placements[player].append((token, placed_country))
    
    # TOKEN SCORING
    player_token_scores = {p: 0 for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        for token_type, placed_country in player_token_placements[player]:
            if placed_country == champion_country:
                bonus = token_values[token_type]['bonus']
                player_token_scores[player] += bonus
                
                if champion_owner is not None and champion_owner != player:
                    penalty = token_values[token_type]['penalty']
                    player_token_scores[champion_owner] -= penalty
    
    # TOTAL SCORES
    player_total_scores = {}
    for player in PLAYER_ORDER:
        player_total_scores[player] = player_base_scores[player] + player_token_scores[player]
    
    return {
        'player_total_scores': player_total_scores,
        'player_tokens': player_tokens
    }

def evaluate_token_values(bronze_bonus, bronze_penalty, silver_bonus, silver_penalty, gold_bonus, gold_penalty):
    """Run full simulation with given token values and return fairness metric"""
    
    token_values = {
        'Bronze': {'bonus': bronze_bonus, 'penalty': bronze_penalty},
        'Silver': {'bonus': silver_bonus, 'penalty': silver_penalty},
        'Gold': {'bonus': gold_bonus, 'penalty': gold_penalty}
    }
    
    years = sorted(df['year'].unique())
    all_scores = defaultdict(list)
    
    for year in years:
        year_data = df[df['year'] == year]
        result = simulate_year(year_data, token_values)
        if result is not None:
            for player in PLAYER_ORDER:
                all_scores[player].append(result['player_total_scores'][player])
    
    # Calculate average scores
    avg_scores = {p: np.mean(all_scores[p]) for p in PLAYER_ORDER}
    
    # Fairness metrics
    std_dev = np.std(list(avg_scores.values()))
    score_range = max(avg_scores.values()) - min(avg_scores.values())
    
    return std_dev, score_range, avg_scores

print('=== Optimizing Fantasy League Token Values ===\n')

# Define search space (reduced for faster execution)
bronze_bonus_values = [0, 10, 20]
bronze_penalty_values = [0]
silver_bonus_values = [100, 200, 300]
silver_penalty_values = [0, 20, 40]
gold_bonus_values = [200, 400, 600, 800, 1000, 1200, 1400]
gold_penalty_values = [0, 100, 200]

total_combinations = (len(bronze_bonus_values) * len(bronze_penalty_values) * 
                     len(silver_bonus_values) * len(silver_penalty_values) *
                     len(gold_bonus_values) * len(gold_penalty_values))

print(f'Testing {total_combinations} token value combinations...')
print(f'This will take a few minutes...\n')

best_results = []
tested = 0

for bb, bp, sb, sp, gb, gp in product(bronze_bonus_values, bronze_penalty_values,
                                      silver_bonus_values, silver_penalty_values,
                                      gold_bonus_values, gold_penalty_values):
    std_dev, score_range, avg_scores = evaluate_token_values(bb, bp, sb, sp, gb, gp)
    
    best_results.append({
        'bronze_bonus': bb,
        'bronze_penalty': bp,
        'silver_bonus': sb,
        'silver_penalty': sp,
        'gold_bonus': gb,
        'gold_penalty': gp,
        'std_dev': std_dev,
        'range': score_range,
        'avg_scores': avg_scores
    })
    
    tested += 1
    if tested % 500 == 0:
        print(f'  Tested {tested}/{total_combinations}...')

# Sort by standard deviation
results_df = pd.DataFrame(best_results)
results_df = results_df.sort_values('std_dev')

print(f'\n=== Top 20 Most Fair Token Value Combinations ===')
print(f'(Sorted by standard deviation - lower is more fair)\n')

for i, row in results_df.head(20).iterrows():
    rank = results_df.index.get_loc(i) + 1
    print(f'#{rank}:')
    print(f'  Bronze: +{row["bronze_bonus"]}/-{row["bronze_penalty"]}')
    print(f'  Silver: +{row["silver_bonus"]}/-{row["silver_penalty"]}')
    print(f'  Gold: +{row["gold_bonus"]}/-{row["gold_penalty"]}')
    print(f'  Std Dev: {row["std_dev"]:.1f}')
    print(f'  Range: {row["range"]:.1f}')
    
    # Show player scores
    scores = row['avg_scores']
    sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    score_str = ', '.join([f'{p}:{s:.0f}' for p, s in sorted_players])
    print(f'  Scores: {score_str}')
    print()

# Compare to baseline and current system
print('\n=== Comparison ===\n')

baseline = results_df[
    (results_df['bronze_bonus'] == 0) & 
    (results_df['silver_bonus'] == 0) & 
    (results_df['gold_bonus'] == 0)
].iloc[0]

print(f'Baseline (no tokens):')
print(f'  Std Dev: {baseline["std_dev"]:.1f}')
print(f'  Range: {baseline["range"]:.1f}')

current = results_df[
    (results_df['bronze_bonus'] == 5) & (results_df['bronze_penalty'] == 0) &
    (results_df['silver_bonus'] == 100) & (results_df['silver_penalty'] == 20) &
    (results_df['gold_bonus'] == 250) & (results_df['gold_penalty'] == 100)
]

if len(current) > 0:
    current = current.iloc[0]
    rank = results_df.index.get_loc(current.name) + 1
    print(f'\nCurrent system (Bronze: +5/-0, Silver: +100/-20, Gold: +250/-100):')
    print(f'  Rank: #{rank} out of {len(results_df)}')
    print(f'  Std Dev: {current["std_dev"]:.1f}')
    print(f'  Range: {current["range"]:.1f}')

best = results_df.iloc[0]
print(f'\nOptimal token values:')
print(f'  Bronze: +{best["bronze_bonus"]:.0f}/-{best["bronze_penalty"]:.0f}')
print(f'  Silver: +{best["silver_bonus"]:.0f}/-{best["silver_penalty"]:.0f}')
print(f'  Gold: +{best["gold_bonus"]:.0f}/-{best["gold_penalty"]:.0f}')
print(f'  Std Dev: {best["std_dev"]:.1f} ({((best["std_dev"] - baseline["std_dev"]) / baseline["std_dev"] * 100):.1f}% vs baseline)')
print(f'  Range: {best["range"]:.1f} ({((best["range"] - baseline["range"]) / baseline["range"] * 100):.1f}% vs baseline)')

# Save results
results_df.to_csv('fantasy_token_optimization_results.csv', index=False)
print(f'\nFull results saved to: fantasy_token_optimization_results.csv')
