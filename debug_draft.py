import pandas as pd
import numpy as np

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

# Get 2023 data
year_2023 = df[df['year'] == 2023]

semi1 = year_2023[year_2023['semi_final'].astype(str) == '1'].copy()
semi2 = year_2023[year_2023['semi_final'].astype(str) == '2'].copy()

print('=== 2023 DRAFT POOLS ===\n')

print(f'SEMI 1 POOL ({len(semi1)} countries):')
print(semi1[['country', 'tier', 'cluster', 'direct_qualifier_10', 'semi_total_points']].sort_values('semi_total_points', ascending=False))

print(f'\n\nSEMI 2 POOL ({len(semi2)} countries):')
print(semi2[['country', 'tier', 'cluster', 'direct_qualifier_10', 'semi_total_points']].sort_values('semi_total_points', ascending=False))

# Count tiers in each pool
print('\n\n=== TIER DISTRIBUTION ===')
print('\nSemi 1:')
print(semi1['tier'].value_counts().sort_index())
print(f'Direct qualifiers: {(semi1["direct_qualifier_10"] == 1).sum()}')

print('\nSemi 2:')
print(semi2['tier'].value_counts().sort_index())
print(f'Direct qualifiers: {(semi2["direct_qualifier_10"] == 1).sum()}')

# Simulate draft picking pattern
PLAYER_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
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

# DRAFT 1
print('\n\n=== DRAFT 1 (Semi 1 Pool) ===')
draft1_order = PLAYER_ORDER + PLAYER_ORDER[::-1]
drafted_countries = []
draft1_picks = {}

for i, player in enumerate(draft1_order):
    available = semi1[~semi1['country'].isin(drafted_countries)]
    pick = pick_country(available, PLAYERS[player]['strategy'])
    if pick is not None:
        if player not in draft1_picks:
            draft1_picks[player] = []
        draft1_picks[player].append(pick)
        drafted_countries.append(pick['country'])
        print(f"Pick {i+1:2d} - Player {player} ({PLAYERS[player]['strategy']}): {pick['country']:20s} Tier {pick['tier']} Score {pick['semi_total_points']:.0f}")

# DRAFT 2
print('\n\n=== DRAFT 2 (Semi 2 Pool) ===')
draft2_order = PLAYER_ORDER[::-1] + PLAYER_ORDER
draft2_picks = {}

for i, player in enumerate(draft2_order):
    available = semi2[~semi2['country'].isin(drafted_countries)]
    pick = pick_country(available, PLAYERS[player]['strategy'])
    if pick is not None:
        if player not in draft2_picks:
            draft2_picks[player] = []
        draft2_picks[player].append(pick)
        drafted_countries.append(pick['country'])
        print(f"Pick {i+1:2d} - Player {player} ({PLAYERS[player]['strategy']}): {pick['country']:20s} Tier {pick['tier']} Score {pick['semi_total_points']:.0f}")

# Show final rosters
print('\n\n=== FINAL DRAFT ROSTERS ===')
for player in PLAYER_ORDER:
    picks1 = draft1_picks.get(player, [])
    picks2 = draft2_picks.get(player, [])
    all_picks = picks1 + picks2
    total_semi = sum(p['semi_total_points'] for p in all_picks)
    print(f"\nPlayer {player}: {len(all_picks)} countries, Total Semi Score: {total_semi:.0f}")
    for p in all_picks:
        print(f"  - {p['country']:20s} Tier {p['tier']} Semi: {p['semi_total_points']:.0f} Final: {p['final_total_points']:.0f} Qualified: {p['qualified_10']}")
