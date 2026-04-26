import pandas as pd
import numpy as np
from collections import defaultdict

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

# Assign tiers
df['tier'] = 0
TIER1_SIZE = 10
TIER2_SIZE = 10

for year in df['year'].unique():
    year_mask = df['year'] == year
    year_data = df[year_mask].copy()
    
    direct_qual_mask = year_mask & (df['direct_qualifier_10'] == 1)
    df.loc[direct_qual_mask, 'tier'] = 1
    num_tier1 = direct_qual_mask.sum()
    
    non_dq = year_data[year_data['direct_qualifier_10'] == 0].copy()
    non_dq = non_dq.sort_values('semi_total_points', ascending=False)
    
    tier1_needed = max(0, TIER1_SIZE - num_tier1)
    if tier1_needed > 0 and len(non_dq) > 0:
        tier1_adds = non_dq.iloc[:tier1_needed]
        for idx in tier1_adds.index:
            df.loc[idx, 'tier'] = 1
    
    tier2_start = tier1_needed
    tier2_end = tier2_start + TIER2_SIZE
    if len(non_dq) > tier2_start:
        tier2_countries = non_dq.iloc[tier2_start:tier2_end]
        for idx in tier2_countries.index:
            df.loc[idx, 'tier'] = 2
    
    tier3_start = tier2_end
    if len(non_dq) > tier3_start:
        tier3_countries = non_dq.iloc[tier3_start:]
        for idx in tier3_countries.index:
            df.loc[idx, 'tier'] = 3

TOKEN_VALUES = {
    'Bronze': {'bonus': 5, 'penalty': 2},
    'Silver': {'bonus': 50, 'penalty': 25},
    'Gold': {'bonus': 250, 'penalty': 125}
}

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

def simulate_year_old_rules(year_data):
    """Original rules: penalties only on winner"""
    return simulate_year(year_data, penalty_all=False)

def simulate_year_new_rules(year_data):
    """New rules: penalties on ANY token placement"""
    return simulate_year(year_data, penalty_all=True)

def simulate_year(year_data, penalty_all=False):
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
    
    # Token minting
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
    
    # Token minting
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 2 or semi_val == '2':
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = TIER_TO_TOKEN[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # Qualifiers and rescue
    player_qualifiers = {}
    for player in PLAYER_ORDER:
        qualifiers = [c for c in player_countries[player] 
                     if c['qualified_10'] == 1 or c['direct_qualifier_10'] == 1]
        player_qualifiers[player] = qualifiers
    
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
    
    # Final roster
    player_final_roster = {}
    for player in PLAYER_ORDER:
        if len(player_qualifiers[player]) >= 3:
            sorted_qual = sorted(player_qualifiers[player], 
                               key=lambda x: x['final_total_points'], reverse=True)
            player_final_roster[player] = sorted_qual[:3]
        else:
            player_final_roster[player] = player_qualifiers[player]
    
    # Build ownership map
    country_to_owner = {}
    for player in PLAYER_ORDER:
        for country_row in player_final_roster[player]:
            country_to_owner[country_row['country']] = player
    
    # Base scores
    player_base_scores = {}
    for player in PLAYER_ORDER:
        player_base_scores[player] = sum(c['final_total_points'] for c in player_final_roster[player])
    
    # Find champion
    champion_row = year_data[year_data['is_champion'] == 1].iloc[0]
    champion_country = champion_row['country']
    champion_owner = country_to_owner.get(champion_country)
    
    # TOKEN PLACEMENT
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
    
    # SCORING
    player_token_scores = {p: 0 for p in PLAYER_ORDER}
    player_token_bonuses = {p: 0 for p in PLAYER_ORDER}
    player_token_penalties = {p: 0 for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        for token_type, placed_country in player_token_placements[player]:
            # Find who owns this country
            country_owner = country_to_owner.get(placed_country)
            
            if penalty_all:
                # NEW RULES: Penalty applies to ANY token placement
                if country_owner is not None and country_owner != player:
                    penalty = TOKEN_VALUES[token_type]['penalty']
                    player_token_scores[country_owner] -= penalty
                    player_token_penalties[country_owner] += penalty
            
            # Bonus only if placed on actual winner
            if placed_country == champion_country:
                bonus = TOKEN_VALUES[token_type]['bonus']
                player_token_scores[player] += bonus
                player_token_bonuses[player] += bonus
                
                if not penalty_all:
                    # OLD RULES: Penalty only on winner
                    if champion_owner is not None and champion_owner != player:
                        penalty = TOKEN_VALUES[token_type]['penalty']
                        player_token_scores[champion_owner] -= penalty
                        player_token_penalties[champion_owner] += penalty
    
    # Total scores
    player_total_scores = {}
    for player in PLAYER_ORDER:
        player_total_scores[player] = player_base_scores[player] + player_token_scores[player]
    
    return {
        'player_base_scores': player_base_scores,
        'player_token_scores': player_token_scores,
        'player_token_bonuses': player_token_bonuses,
        'player_token_penalties': player_token_penalties,
        'player_total_scores': player_total_scores
    }

# Run both simulations
print("="*80)
print("COMPARING PENALTY RULES")
print("="*80)

years = sorted(df['year'].unique())

results_old = []
results_new = []

for year in years:
    year_data = df[df['year'] == year]
    
    result_old = simulate_year_old_rules(year_data)
    result_new = simulate_year_new_rules(year_data)
    
    if result_old is not None and result_new is not None:
        results_old.append(result_old)
        results_new.append(result_new)

# Aggregate
all_scores_old = defaultdict(list)
all_bonuses_old = defaultdict(list)
all_penalties_old = defaultdict(list)

all_scores_new = defaultdict(list)
all_bonuses_new = defaultdict(list)
all_penalties_new = defaultdict(list)

for result in results_old:
    for player in PLAYER_ORDER:
        all_scores_old[player].append(result['player_total_scores'][player])
        all_bonuses_old[player].append(result['player_token_bonuses'][player])
        all_penalties_old[player].append(result['player_token_penalties'][player])

for result in results_new:
    for player in PLAYER_ORDER:
        all_scores_new[player].append(result['player_total_scores'][player])
        all_bonuses_new[player].append(result['player_token_bonuses'][player])
        all_penalties_new[player].append(result['player_token_penalties'][player])

print("\n### OLD RULES: Penalties only on Eurovision winner ###\n")
print(f'{"Player":<8} {"Strategy":<10} {"Base":<10} {"Bonuses":<10} {"Penalties":<10} {"Net":<10} {"Total":<10}')
print("="*80)

for player in PLAYER_ORDER:
    avg_base = np.mean([r['player_base_scores'][player] for r in results_old])
    avg_bonuses = np.mean(all_bonuses_old[player])
    avg_penalties = np.mean(all_penalties_old[player])
    avg_net = avg_bonuses - avg_penalties
    avg_total = np.mean(all_scores_old[player])
    print(f'{player:<8} {PLAYERS[player]["strategy"]:<10} {avg_base:>9.1f} {avg_bonuses:>9.1f} {avg_penalties:>9.1f} {avg_net:>9.1f} {avg_total:>9.1f}')

avg_scores_old = [np.mean(all_scores_old[p]) for p in PLAYER_ORDER]
std_dev_old = np.std(avg_scores_old)
range_old = max(avg_scores_old) - min(avg_scores_old)

print(f'\nStd Dev: {std_dev_old:.1f}, Range: {range_old:.1f}')

print("\n" + "="*80)
print("### NEW RULES: Penalties on ANY token placement ###\n")
print(f'{"Player":<8} {"Strategy":<10} {"Base":<10} {"Bonuses":<10} {"Penalties":<10} {"Net":<10} {"Total":<10}')
print("="*80)

for player in PLAYER_ORDER:
    avg_base = np.mean([r['player_base_scores'][player] for r in results_new])
    avg_bonuses = np.mean(all_bonuses_new[player])
    avg_penalties = np.mean(all_penalties_new[player])
    avg_net = avg_bonuses - avg_penalties
    avg_total = np.mean(all_scores_new[player])
    print(f'{player:<8} {PLAYERS[player]["strategy"]:<10} {avg_base:>9.1f} {avg_bonuses:>9.1f} {avg_penalties:>9.1f} {avg_net:>9.1f} {avg_total:>9.1f}')

avg_scores_new = [np.mean(all_scores_new[p]) for p in PLAYER_ORDER]
std_dev_new = np.std(avg_scores_new)
range_new = max(avg_scores_new) - min(avg_scores_new)

print(f'\nStd Dev: {std_dev_new:.1f}, Range: {range_new:.1f}')

print("\n" + "="*80)
print("COMPARISON SUMMARY")
print("="*80)
print(f"\nOLD RULES: Std Dev = {std_dev_old:.1f}, Range = {range_old:.1f}")
print(f"NEW RULES: Std Dev = {std_dev_new:.1f}, Range = {range_new:.1f}")
print(f"\nChange: {((std_dev_new - std_dev_old) / std_dev_old * 100):+.1f}% std dev, {((range_new - range_old) / range_old * 100):+.1f}% range")
