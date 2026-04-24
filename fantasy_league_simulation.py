import pandas as pd
import numpy as np
from collections import defaultdict

# Set random seed for reproducibility
np.random.seed(42)

# Read the normalized clustering data
df = pd.read_csv('data/song_data_clustered_semi_normalized.csv')

print('=== Eurovision Fantasy League Simulation ===')
print('Following actual game rules with 8 players\n')

# Assign proxy semi scores to direct qualifiers FIRST (before tier assignment)
# Use median of top 10 semi scores from their year
print('Assigning proxy semi scores to direct qualifiers...')
for year in df['year'].unique():
    year_mask = df['year'] == year
    
    # Get top 10 semi scores from non-direct qualifiers
    semi_mask = year_mask & (df['direct_qualifier_10'] == 0) & (df['semi_total_points'].notna())
    if semi_mask.any():
        top_semi_scores = df.loc[semi_mask, 'semi_total_points'].nlargest(10)
        proxy_score = top_semi_scores.median()
        
        # Assign to direct qualifiers in this year
        dq_mask = year_mask & (df['semi_total_points'].isna())
        df.loc[dq_mask, 'semi_total_points'] = proxy_score
        
        num_dqs = dq_mask.sum()
        if num_dqs > 0:
            print(f'  {year}: {num_dqs} direct qualifiers assigned semi score {proxy_score:.0f} (median of top 10)')

# Verification: Check if any NaN values remain
remaining_nans = df['semi_total_points'].isna().sum()
if remaining_nans > 0:
    print(f'\nWARNING: {remaining_nans} countries still have NaN semi_total_points!')
else:
    print(f'✓ All {len(df)} countries have semi_total_points assigned')

# Assign tiers based on ranking within each year
# Tier 1: 10 countries (direct qualifiers + top semi scores to reach 10) → Bronze
# Tier 2: Next 10 highest semi scores → Silver
# Tier 3: Remaining countries → Gold
print('\nAssigning tiers by year ranking...')
df['tier'] = 0  # Initialize

TIER1_SIZE = 10
TIER2_SIZE = 10

for year in df['year'].unique():
    year_mask = df['year'] == year
    year_data = df[year_mask].copy()
    
    # Start with direct qualifiers in Tier 1
    direct_qual_mask = year_mask & (df['direct_qualifier_10'] == 1)
    df.loc[direct_qual_mask, 'tier'] = 1
    num_tier1 = direct_qual_mask.sum()
    
    # Get non-direct qualifiers sorted by semi score
    non_dq = year_data[year_data['direct_qualifier_10'] == 0].copy()
    non_dq = non_dq.sort_values('semi_total_points', ascending=False)
    
    # Fill Tier 1 to target size
    tier1_needed = max(0, TIER1_SIZE - num_tier1)
    if tier1_needed > 0 and len(non_dq) > 0:
        tier1_adds = non_dq.iloc[:tier1_needed]
        for idx in tier1_adds.index:
            df.loc[idx, 'tier'] = 1
    
    # Next TIER2_SIZE = Tier 2
    tier2_start = tier1_needed
    tier2_end = tier2_start + TIER2_SIZE
    if len(non_dq) > tier2_start:
        tier2_countries = non_dq.iloc[tier2_start:tier2_end]
        for idx in tier2_countries.index:
            df.loc[idx, 'tier'] = 2
    
    # Rest = Tier 3
    tier3_start = tier2_end
    if len(non_dq) > tier3_start:
        tier3_countries = non_dq.iloc[tier3_start:]
        for idx in tier3_countries.index:
            df.loc[idx, 'tier'] = 3
    
    print(f'  {year}: Tier 1={df[year_mask & (df["tier"]==1)].shape[0]}, Tier 2={df[year_mask & (df["tier"]==2)].shape[0]}, Tier 3={df[year_mask & (df["tier"]==3)].shape[0]}')

print()

# Token values - OPTIMIZED FOR BALANCE
# Based on simulation testing with correct token placement mechanics
# Players predict champion from top 3 finishers (~33% success rate)
TOKEN_VALUES = {
    'Bronze': {'bonus': 5, 'penalty': 2},
    'Silver': {'bonus': 50, 'penalty': 25},
    'Gold': {'bonus': 250, 'penalty': 125}
}

TIER_TO_TOKEN = {1: 'Bronze', 2: 'Silver', 3: 'Gold'}

# Player strategies
PLAYERS = {
    'A': {'name': 'Player A', 'strategy': 'tier1', 'desc': 'Bold for high value (Tier 1)'},
    'B': {'name': 'Player B', 'strategy': 'tier1', 'desc': 'Bold for high value (Tier 1)'},
    'C': {'name': 'Player C', 'strategy': 'tier1', 'desc': 'Bold for high value (Tier 1)'},
    'D': {'name': 'Player D', 'strategy': 'tier2', 'desc': 'Safe (Tier 2)'},
    'E': {'name': 'Player E', 'strategy': 'tier2', 'desc': 'Safe (Tier 2)'},
    'F': {'name': 'Player F', 'strategy': 'tier2', 'desc': 'Safe (Tier 2)'},
    'G': {'name': 'Player G', 'strategy': 'tier3', 'desc': 'Bold for low value (Tier 3)'},
    'H': {'name': 'Player H', 'strategy': 'tier3', 'desc': 'Bold for low value (Tier 3)'}
}

PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

def pick_country(available_pool, strategy):
    """Pick best country from pool based on strategy and semi scores"""
    if len(available_pool) == 0:
        return None
    
    # Determine preferred tier based on strategy
    if strategy == 'tier1':
        preferred_tier = 1
    elif strategy == 'tier2':
        preferred_tier = 2
    else:  # tier3
        preferred_tier = 3
    
    # Try to pick from preferred tier first (highest semi score)
    preferred = available_pool[available_pool['tier'] == preferred_tier]
    if len(preferred) > 0:
        return preferred.nlargest(1, 'semi_total_points', keep='first').iloc[0]
    
    # Fallback: pick highest semi score from any tier
    return available_pool.nlargest(1, 'semi_total_points', keep='first').iloc[0]

def simulate_year(year_data):
    """Simulate one year of the fantasy league"""
    
    # Separate by semi-final
    # Note: Direct qualifiers are now randomly assigned to semi 1 or 2
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    
    if len(semi1) < 8 or len(semi2) < 8:
        return None  # Not enough countries to draft
    
    # Initialize player data
    player_countries = {p: [] for p in PLAYER_ORDER}
    player_tokens = {p: {'Bronze': 0, 'Silver': 0, 'Gold': 0} for p in PLAYER_ORDER}
    drafted_countries = []
    
    # DRAFT 1: Before Semi-Final 1 (2 picks each, snake order)
    draft1_order = PLAYER_ORDER + PLAYER_ORDER[::-1]  # A-B-C-D-E-F-G-H-H-G-F-E-D-C-B-A
    
    # Pool: Semi 1 only (includes any direct qualifiers assigned to Semi 1)
    draft1_pool = semi1.copy()
    
    for player in draft1_order:
        available = draft1_pool[~draft1_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI-FINAL 1: Mint tokens for qualifiers
    # Direct qualifiers always qualify (direct_qualifier_10 == 1)
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            # Debug: Check data type and condition
            semi_val = country_row['semi_final']
            if semi_val == 1 or semi_val == '1':  # Handle both numeric and string
                # Check if qualified (either through semi or as direct qualifier)
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = TIER_TO_TOKEN[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # DRAFT 2: Before Semi-Final 2 (2 more picks each, snake order reversed from Draft 1)
    draft2_order = PLAYER_ORDER[::-1] + PLAYER_ORDER  # H-G-F-E-D-C-B-A-A-B-C-D-E-F-G-H
    
    # Pool: Semi 2 only (Semi 1 already happened, direct qualifiers already drafted)
    draft2_pool = semi2.copy()
    
    for player in draft2_order:
        available = draft2_pool[~draft2_pool['country'].isin(drafted_countries)]
        pick = pick_country(available, PLAYERS[player]['strategy'])
        if pick is not None:
            player_countries[player].append(pick)
            drafted_countries.append(pick['country'])
    
    # SEMI-FINAL 2: Mint tokens for qualifiers
    # Direct qualifiers always qualify (direct_qualifier_10 == 1)
    for player in PLAYER_ORDER:
        for country_row in player_countries[player]:
            semi_val = country_row['semi_final']
            if semi_val == 2 or semi_val == '2':  # Handle both numeric and string
                # Check if qualified (either through semi or as direct qualifier)
                if country_row['qualified_10'] == 1 or country_row['direct_qualifier_10'] == 1:
                    token_type = TIER_TO_TOKEN[country_row['tier']]
                    player_tokens[player][token_type] += 1
    
    # POST-SEMI CLEANUP: Count qualifiers per player
    player_qualifiers = {}
    for player in PLAYER_ORDER:
        qualifiers = [c for c in player_countries[player] 
                     if c['qualified_10'] == 1 or c['direct_qualifier_10'] == 1]
        player_qualifiers[player] = qualifiers
    
    # RESCUE DRAFT: Players with <3 qualifiers draft from unowned qualifiers
    all_qualifiers = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
    ].copy()
    
    for player in PLAYER_ORDER:
        while len(player_qualifiers[player]) < 3:
            available_rescue = all_qualifiers[~all_qualifiers['country'].isin(drafted_countries)]
            if len(available_rescue) == 0:
                break  # No more countries available
            
            # Pick highest semi score available
            rescue_pick = available_rescue.nlargest(1, 'semi_total_points', keep='first').iloc[0]
            player_countries[player].append(rescue_pick)
            player_qualifiers[player].append(rescue_pick)
            drafted_countries.append(rescue_pick['country'])
            # Rescue picks don't mint tokens
    
    # FINAL ROSTER LOCK: Select best 3 qualifiers
    player_final_roster = {}
    for player in PLAYER_ORDER:
        if len(player_qualifiers[player]) >= 3:
            # Pick top 3 by final_total_points
            sorted_qual = sorted(player_qualifiers[player], 
                               key=lambda x: x['final_total_points'], reverse=True)
            player_final_roster[player] = sorted_qual[:3]
        else:
            player_final_roster[player] = player_qualifiers[player]
    
    # Calculate base score (sum of 3 locked countries)
    player_base_scores = {}
    for player in PLAYER_ORDER:
        player_base_scores[player] = sum(c['final_total_points'] for c in player_final_roster[player])
    
    # Find the champion
    champion_row = year_data[year_data['is_champion'] == 1].iloc[0]
    champion_country = champion_row['country']
    champion_owner = None
    
    for player in PLAYER_ORDER:
        roster_countries = [c['country'] for c in player_final_roster[player]]
        if champion_country in roster_countries:
            champion_owner = player
            break
    
    # TOKEN PLACEMENT: Players predict the Eurovision champion
    # They can place tokens on ANY country in the Grand Final (not just their own)
    # Strategy: Players see performances and predict from top finishers
    player_token_placements = {p: [] for p in PLAYER_ORDER}
    
    # Get all countries that qualified to the Grand Final
    all_qualifiers = year_data[
        (year_data['qualified_10'] == 1) | (year_data['direct_qualifier_10'] == 1)
    ].copy()
    
    # Identify top 3 actual finishers (players would know these performed well)
    top_3_finishers = all_qualifiers.nlargest(3, 'final_total_points')['country'].tolist()
    
    for player in PLAYER_ORDER:
        tokens_to_place = []
        for token_type, count in player_tokens[player].items():
            tokens_to_place.extend([token_type] * count)
        
        if len(tokens_to_place) > 0:
            # Players intelligently pick from top 3 finishers
            # (simulating they saw performances and can guess well)
            # Equal probability among top 3
            for token in tokens_to_place:
                predicted_champion = np.random.choice(top_3_finishers)
                player_token_placements[player].append((token, predicted_champion))
    
    # FINAL SCORING: Calculate token bonuses/penalties
    player_token_scores = {p: 0 for p in PLAYER_ORDER}
    player_token_bonuses = {p: 0 for p in PLAYER_ORDER}
    player_token_penalties = {p: 0 for p in PLAYER_ORDER}
    
    for player in PLAYER_ORDER:
        for token_type, placed_country in player_token_placements[player]:
            if placed_country == champion_country:
                # Token activates!
                bonus = TOKEN_VALUES[token_type]['bonus']
                player_token_scores[player] += bonus
                player_token_bonuses[player] += bonus
                
                # Apply penalty to champion owner
                if champion_owner is not None and champion_owner != player:
                    penalty = TOKEN_VALUES[token_type]['penalty']
                    player_token_scores[champion_owner] -= penalty
                    player_token_penalties[champion_owner] += penalty
    
    # Total scores
    player_total_scores = {}
    for player in PLAYER_ORDER:
        player_total_scores[player] = player_base_scores[player] + player_token_scores[player]
    
    return {
        'year': int(year_data['year'].iloc[0]),
        'champion': champion_country,
        'champion_owner': champion_owner,
        'player_base_scores': player_base_scores,
        'player_token_scores': player_token_scores,
        'player_token_bonuses': player_token_bonuses,
        'player_token_penalties': player_token_penalties,
        'player_total_scores': player_total_scores,
        'player_tokens': player_tokens,
        'player_final_roster': player_final_roster
    }

# Run simulation for all years
years = sorted(df['year'].unique())
results = []

print('Simulating years...')
for year in years:
    year_data = df[df['year'] == year]
    result = simulate_year(year_data)
    if result is not None:
        results.append(result)
        print(f'  {year}: {result["champion"]} (owned by {result["champion_owner"] or "nobody"})')

print(f'\n{len(results)} years simulated successfully\n')

# Aggregate results
all_scores = defaultdict(list)
all_base_scores = defaultdict(list)
all_token_scores = defaultdict(list)
all_token_bonuses = defaultdict(list)
all_token_penalties = defaultdict(list)

for result in results:
    for player in PLAYER_ORDER:
        all_scores[player].append(result['player_total_scores'][player])
        all_base_scores[player].append(result['player_base_scores'][player])
        all_token_scores[player].append(result['player_token_scores'][player])
        all_token_bonuses[player].append(result['player_token_bonuses'][player])
        all_token_penalties[player].append(result['player_token_penalties'][player])

# Calculate averages
print('=== Detailed Score Breakdown by Player ===\n')
print(f'{"Player":<8} {"Strategy":<10} {"Base Score":<12} {"+ Bonuses":<12} {"- Penalties":<12} {"= Net Tokens":<14} {"Total":<10}')
print('=' * 90)

for player in PLAYER_ORDER:
    avg_base = np.mean(all_base_scores[player])
    avg_bonuses = np.mean(all_token_bonuses[player])
    avg_penalties = np.mean(all_token_penalties[player])
    avg_tokens = np.mean(all_token_scores[player])
    avg_total = np.mean(all_scores[player])
    print(f'{player:<8} {PLAYERS[player]["strategy"]:<10} {avg_base:>11.1f} {avg_bonuses:>11.1f} {avg_penalties:>11.1f} {avg_tokens:>13.1f} {avg_total:>9.1f}')

print(f'\n{"":>29} {"(from picks)":<12} {"(token wins)":<12} {"(paid out)":<12} {"(bonuses-pen)":<14}')

print('\n=== Summary Statistics ===\n')
print(f'Standard deviation of total scores: {np.std([np.mean(all_scores[p]) for p in PLAYER_ORDER]):.1f}')
print(f'Range (max - min): {max([np.mean(all_scores[p]) for p in PLAYER_ORDER]) - min([np.mean(all_scores[p]) for p in PLAYER_ORDER]):.1f}')

# Show token distribution
print('\n=== Average Tokens Minted by Player ===\n')
print(f'{"Player":<10} {"Bronze":<10} {"Silver":<10} {"Gold":<10}')
print('-' * 40)

avg_tokens = defaultdict(lambda: {'Bronze': 0, 'Silver': 0, 'Gold': 0})
for result in results:
    for player in PLAYER_ORDER:
        for token_type in ['Bronze', 'Silver', 'Gold']:
            avg_tokens[player][token_type] += result['player_tokens'][player][token_type]

for player in PLAYER_ORDER:
    bronze = avg_tokens[player]['Bronze'] / len(results)
    silver = avg_tokens[player]['Silver'] / len(results)
    gold = avg_tokens[player]['Gold'] / len(results)
    print(f'{player:<10} {bronze:>9.2f} {silver:>9.2f} {gold:>9.2f}')

print(f'\n=== Current Token Values ===')
print(f'Bronze: +{TOKEN_VALUES["Bronze"]["bonus"]}/-{TOKEN_VALUES["Bronze"]["penalty"]}')
print(f'Silver: +{TOKEN_VALUES["Silver"]["bonus"]}/-{TOKEN_VALUES["Silver"]["penalty"]}')
print(f'Gold: +{TOKEN_VALUES["Gold"]["bonus"]}/-{TOKEN_VALUES["Gold"]["penalty"]}')
