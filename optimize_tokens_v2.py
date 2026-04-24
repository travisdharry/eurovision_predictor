import pandas as pd
import numpy as np
from collections import defaultdict
import itertools

# Set random seed for reproducibility
np.random.seed(42)

# Read the data
df = pd.read_csv('data/song_data_clustered_semi_normalized.csv')

# Assign proxy semi scores to direct qualifiers
for year in df['year'].unique():
    year_mask = df['year'] == year
    semi_mask = year_mask & (df['direct_qualifier_10'] == 0) & (df['semi_total_points'].notna())
    if semi_mask.any():
        top_semi_scores = df.loc[semi_mask, 'semi_total_points'].nlargest(10)
        proxy_score = top_semi_scores.median()
        dq_mask = year_mask & (df['semi_total_points'].isna())
        df.loc[dq_mask, 'semi_total_points'] = proxy_score

# Assign tiers based on year ranking
df['tier'] = 0
for year in df['year'].unique():
    year_mask = df['year'] == year
    year_data = df[year_mask].copy()
    
    direct_qual_mask = year_mask & (df['direct_qualifier_10'] == 1)
    df.loc[direct_qual_mask, 'tier'] = 1
    num_tier1 = direct_qual_mask.sum()
    
    non_dq = year_data[year_data['direct_qualifier_10'] == 0].copy()
    non_dq = non_dq.sort_values('semi_total_points', ascending=False)
    
    tier1_needed = max(0, 10 - num_tier1)
    if tier1_needed > 0 and len(non_dq) > 0:
        tier1_adds = non_dq.iloc[:tier1_needed]
        for idx in tier1_adds.index:
            df.loc[idx, 'tier'] = 1
    
    tier2_start = tier1_needed
    tier2_end = tier2_start + 10
    if len(non_dq) > tier2_start:
        tier2_countries = non_dq.iloc[tier2_start:tier2_end]
        for idx in tier2_countries.index:
            df.loc[idx, 'tier'] = 2
    
    tier3_start = tier2_end
    if len(non_dq) > tier3_start:
        tier3_countries = non_dq.iloc[tier3_start:]
        for idx in tier3_countries.index:
            df.loc[idx, 'tier'] = 3

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}

PLAYERS = {
    'A': {'strategy': 'tier1'},
    'B': {'strategy': 'tier1'},
    'C': {'strategy': 'tier1'},
    'D': {'strategy': 'tier2'},
    'E': {'strategy': 'tier2'},
    'F': {'strategy': 'tier2'},
    'G': {'strategy': 'tier3'},
    'H': {'strategy': 'tier3'}
}

PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def pick_country(available_pool, strategy):
    if len(available_pool) == 0:
        return None
    
    if strategy == 'tier1':
        preferred_tier = 1
    elif strategy == 'tier2':
        preferred_tier = 2
    else:
        preferred_tier = 3
    
    preferred = available_pool[available_pool['tier'] == preferred_tier]
    if len(preferred) > 0:
        return preferred.nlargest(1, 'semi_total_points', keep='first').iloc[0]
    
    return available_pool.nlargest(1, 'semi_total_points', keep='first').iloc[0]

def simulate_year(year_data, token_values):
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    
    if len(semi1) < 8 or len(semi2) < 8:
        return None
    
    player_countries = {p: [] for p in PLAYER_ORDER}
    player_tokens = {p: {'Bronze': 0, 'Silver': 0, 'Gold': 0} for p in PLAYER_ORDER}
    drafted_countries = []
    
    # DRAFT 1
    draft1_order = PLAYER_ORDER + PLAYER_ORDER[::-1]
    draft1_pool = semi1.copy()
    
    for player in draft1_order:
        available = draft1_pool[~draft1_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # Token minting after Semi 1
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 1 or semi_val == '1':
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = TIER_TO_TOKEN[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # DRAFT 2
    draft2_order = PLAYER_ORDER[::-1] + PLAYER_ORDER
    draft2_pool = semi2.copy()
    
    for player in draft2_order:
        available = draft2_pool[~draft2_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # Token minting after Semi 2
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 2 or semi_val == '2':
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = TIER_TO_TOKEN[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # Count qualifiers
    player_qualifiers = {}
    for player in PLAYER_ORDER:
        qualifiers = [c for c in player_countries[player] 
                     if c['qualified_10'] == 1 or c['direct_qualifier_10'] == 1]
        player_qualifiers[player] = qualifiers
    
    # Rescue draft
    all_qualifiers = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
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
    
    # Final roster lock
    player_final_roster = {}
    for player in PLAYER_ORDER:
        if len(player_qualifiers[player]) >= 3:
            sorted_qual = sorted(player_qualifiers[player], 
                               key=lambda x: x['final_total_points'], reverse=True)
            player_final_roster[player] = sorted_qual[:3]
        else:
            player_final_roster[player] = player_qualifiers[player]
    
    # Base scores
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
    
    # TOKEN PLACEMENT: Players predict champion from top 3 finishers
    all_qualifiers_list = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
    ].copy()
    top_3_finishers = all_qualifiers_list.nlargest(3, 'final_total_points')['country'].tolist()
    
    player_token_placements = {p: [] for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        tokens_to_place = []
        for token_type, count in player_tokens[player].items():
            tokens_to_place.extend([token_type] * count)
        
        if len(tokens_to_place) > 0:
            for token in tokens_to_place:
                predicted_champion = np.random.choice(top_3_finishers)
                player_token_placements[player].append((token, predicted_champion))
    
    # Calculate token scores
    player_token_scores = {p: 0 for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        for token_type, placed_country in player_token_placements[player]:
            if placed_country == champion_country:
                bonus = token_values[token_type]['bonus']
                player_token_scores[player] += bonus
                
                if champion_owner is not None and champion_owner != player:
                    penalty = token_values[token_type]['penalty']
                    player_token_scores[champion_owner] -= penalty
    
    # Total scores
    player_total_scores = {}
    for player in PLAYER_ORDER:
        player_total_scores[player] = player_base_scores[player] + player_token_scores[player]
    
    return {
        'player_base_scores': player_base_scores,
        'player_token_scores': player_token_scores,
        'player_total_scores': player_total_scores
    }

def evaluate_token_values(bronze_bonus, bronze_penalty, silver_bonus, silver_penalty, gold_bonus, gold_penalty):
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
    
    avg_scores = [np.mean(all_scores[p]) for p in PLAYER_ORDER]
    std_dev = np.std(avg_scores)
    score_range = max(avg_scores) - min(avg_scores)
    
    return {
        'bronze_bonus': bronze_bonus,
        'bronze_penalty': bronze_penalty,
        'silver_bonus': silver_bonus,
        'silver_penalty': silver_penalty,
        'gold_bonus': gold_bonus,
        'gold_penalty': gold_penalty,
        'std_dev': std_dev,
        'range': score_range,
        'avg_scores': avg_scores
    }

print("Testing token value combinations...")
print("Goal: Minimize score variance (std_dev) and range\n")

# Test a range of values focusing on reasonable scales
# Bronze should be small, Silver moderate, Gold high
# Penalties should be proportional to bonuses

test_configs = []

# Conservative values (tokens supplement base scores)
for bronze_b in [5, 10, 15]:
    for silver_b in [50, 100, 150]:
        for gold_b in [150, 200, 250]:
            for penalty_ratio in [0.0, 0.2, 0.5]:  # penalty as % of bonus
                test_configs.append({
                    'bronze_bonus': bronze_b,
                    'bronze_penalty': int(bronze_b * penalty_ratio),
                    'silver_bonus': silver_b,
                    'silver_penalty': int(silver_b * penalty_ratio),
                    'gold_bonus': gold_b,
                    'gold_penalty': int(gold_b * penalty_ratio)
                })

print(f"Testing {len(test_configs)} configurations...")

results = []
for i, config in enumerate(test_configs):
    if i % 10 == 0:
        print(f"  Progress: {i}/{len(test_configs)}")
    
    result = evaluate_token_values(**config)
    results.append(result)

# Sort by std_dev (lower is better)
results.sort(key=lambda x: x['std_dev'])

print(f"\n{'='*80}")
print("TOP 10 MOST BALANCED TOKEN VALUE COMBINATIONS")
print(f"{'='*80}\n")

for i, r in enumerate(results[:10]):
    print(f"#{i+1}: Std Dev = {r['std_dev']:.1f}, Range = {r['range']:.1f}")
    print(f"   Bronze: +{r['bronze_bonus']}/-{r['bronze_penalty']}")
    print(f"   Silver: +{r['silver_bonus']}/-{r['silver_penalty']}")
    print(f"   Gold:   +{r['gold_bonus']}/-{r['gold_penalty']}")
    print(f"   Player scores: {', '.join([f'{s:.0f}' for s in r['avg_scores']])}")
    print()
