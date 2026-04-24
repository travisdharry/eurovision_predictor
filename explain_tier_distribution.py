import pandas as pd

df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Check 2023 as example
year = 2023
year_data = df[df['year'] == year]

print('=== Why Player 4 Gets More Tier 2 Than Player 1 ===\n')

# Confirm direct qualifiers are NOT in semis
dq = year_data[year_data['cluster'] == 3]
print(f'Direct Qualifiers (Cluster 3): {len(dq)} countries')
print(f'Are they in semi-finals? {(dq["semi_final"] != "-").sum()} (should be 0)')
print(f'So Tier 3 is NOT available in the draft!\n')

# Show tier distribution in semis
print('=== 2023 Semi-Final Tier Distribution ===')
semi1 = year_data[year_data['semi_final'].astype(str) == '1']
semi2 = year_data[year_data['semi_final'].astype(str) == '2']

print(f'\nSemi-Final 1: {len(semi1)} total countries')
for cluster in [2, 1, 0]:
    count = len(semi1[semi1['cluster'] == cluster])
    print(f'  Tier {cluster}: {count} countries')

print(f'\nSemi-Final 2: {len(semi2)} total countries')
for cluster in [2, 1, 0]:
    count = len(semi2[semi2['cluster'] == cluster])
    print(f'  Tier {cluster}: {count} countries')

# Show the draft order and what tier they get
print('\n=== Draft Order and Tier Access ===')

semi1_sorted = semi1.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
semi2_sorted = semi2.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)

semi1_draft_order = [1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1]
semi2_draft_order = [8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]

print('\nSemi 1 Draft (first 10 picks):')
for i in range(min(10, len(semi1_sorted))):
    player = semi1_draft_order[i]
    country = semi1_sorted.iloc[i]
    print(f'  Pick {i+1} (Player {player}): Tier {country["cluster"]} - {country["country"]}')

print('\nSemi 2 Draft (first 10 picks):')
for i in range(min(10, len(semi2_sorted))):
    player = semi2_draft_order[i]
    country = semi2_sorted.iloc[i]
    print(f'  Pick {i+1} (Player {player}): Tier {country["cluster"]} - {country["country"]}')

# Show Player 1 vs Player 4 picks
print('\n=== Comparing Player 1 vs Player 4 ===')

print('\nPlayer 1 picks:')
print('  Semi 1: Pick 1 (early Tier 2), Pick 16 (late Tier 0)')
print('  Semi 2: Pick 8 (late Tier 1), Pick 9 (Tier 1 or Tier 0)')

print('\nPlayer 4 picks:')
print('  Semi 1: Pick 4 (early Tier 1), Pick 13 (late Tier 0)')
print('  Semi 2: Pick 5 (early Tier 1), Pick 12 (mid Tier 0)')

# Show actual 2023 results
player1_picks = []
player4_picks = []

for i, player in enumerate(semi1_draft_order[:len(semi1_sorted)]):
    country = semi1_sorted.iloc[i]
    if player == 1:
        player1_picks.append((country['country'], country['cluster'], 'Semi 1'))
    elif player == 4:
        player4_picks.append((country['country'], country['cluster'], 'Semi 1'))

for i, player in enumerate(semi2_draft_order[:len(semi2_sorted)]):
    country = semi2_sorted.iloc[i]
    if player == 1:
        player1_picks.append((country['country'], country['cluster'], 'Semi 2'))
    elif player == 4:
        player4_picks.append((country['country'], country['cluster'], 'Semi 2'))

print('\n=== Actual 2023 Picks ===')
print('\nPlayer 1:')
tier_counts = {0: 0, 1: 0, 2: 0}
for country, tier, semi in player1_picks:
    print(f'  {country} (Tier {tier}) - {semi}')
    tier_counts[tier] += 1
print(f'  Total: {tier_counts[2]} Tier 2, {tier_counts[1]} Tier 1, {tier_counts[0]} Tier 0')

print('\nPlayer 4:')
tier_counts = {0: 0, 1: 0, 2: 0}
for country, tier, semi in player4_picks:
    print(f'  {country} (Tier {tier}) - {semi}')
    tier_counts[tier] += 1
print(f'  Total: {tier_counts[2]} Tier 2, {tier_counts[1]} Tier 1, {tier_counts[0]} Tier 0')

print('\n=== CONCLUSION ===')
print('Player 1 gets only 1 early pick per semi (1st in Semi 1, 8th in Semi 2)')
print('Player 4 gets 2 medium-early picks (4th in Semi 1, 5th in Semi 2)')
print('With ~7 Tier 1 countries per semi, Player 4 often gets Tier 1 in both')
print('While Player 1 gets 1 elite pick but then drops to late picks (16th, 9th)')
