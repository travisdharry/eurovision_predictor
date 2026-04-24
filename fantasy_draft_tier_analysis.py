import pandas as pd
import numpy as np

# Read the clustered data with direct qualifiers as cluster 3
df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Get all years that have both semi-finals
years_with_semis = df[df['semi_final'].astype(str).isin(['1', '2'])]['year'].unique()
years_with_semis = sorted([y for y in years_with_semis if y >= 2009])  # Modern era

print(f'=== Fantasy Draft Analysis: Qualifiers by Tier and Draft Position ===')
print(f'Years analyzed: {len(years_with_semis)} years')

all_picks = []

for YEAR in years_with_semis:
    year_data = df[df['year'] == YEAR].copy()
    
    # Split by semi-final
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    
    # Skip if not enough entries
    if len(semi1) < 15 or len(semi2) < 16:
        continue
    
    # Sort by cluster (high to low) within each semi
    semi1 = semi1.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
    semi2 = semi2.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
    
    # Simulate draft
    semi1_draft_order = [1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1]
    semi2_draft_order = [8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]
    
    # Semi 1 draft
    for pick_num, player in enumerate(semi1_draft_order):
        if pick_num < len(semi1):
            country = semi1.iloc[pick_num]
            all_picks.append({
                'year': YEAR,
                'player': player,
                'semi': 1,
                'pick_num': pick_num + 1,
                'cluster': country['cluster'],
                'qualified': country['qualified_10'],
                'final_points': country['final_total_points']
            })
    
    # Semi 2 draft
    for pick_num, player in enumerate(semi2_draft_order):
        if pick_num < len(semi2):
            country = semi2.iloc[pick_num]
            all_picks.append({
                'year': YEAR,
                'player': player,
                'semi': 2,
                'pick_num': pick_num + 1,
                'cluster': country['cluster'],
                'qualified': country['qualified_10'],
                'final_points': country['final_total_points']
            })

picks_df = pd.DataFrame(all_picks)

print(f'\nTotal picks analyzed: {len(picks_df)}')

# Calculate qualified picks by cluster and player
print(f'\n=== Average Qualifiers Picked by Tier and Draft Position ===')
print('(Tier 0=Low, 1=Medium, 2=High semi performance)\n')

# Create pivot table: player x cluster, counting qualifiers
qualified_by_tier = picks_df[picks_df['qualified'] == 1].groupby(['player', 'cluster']).size().unstack(fill_value=0)

# Get total picks by tier for each player
total_picks_by_tier = picks_df.groupby(['player', 'cluster']).size().unstack(fill_value=0)

# Calculate averages (divide by number of years)
num_years = len(years_with_semis) - 1  # -1 for 2014 skip
qualified_avg = qualified_by_tier / num_years
total_avg = total_picks_by_tier / num_years

print('Average Qualified Picks by Tier:')
print(qualified_avg.round(2).to_string())

print('\n\nAverage Total Picks by Tier:')
print(total_avg.round(2).to_string())

print('\n\nQualification Rate by Tier (% of picks that qualified):')
qual_rate = (qualified_by_tier / total_picks_by_tier * 100).round(1)
print(qual_rate.to_string())

# Summary by player
print(f'\n=== Summary by Draft Position ===')
player_summary = picks_df.groupby('player').agg({
    'qualified': lambda x: (x == 1).sum(),
    'cluster': 'count'
})
player_summary.columns = ['Total Qualifiers', 'Total Picks']
player_summary['Avg Qualifiers/Year'] = (player_summary['Total Qualifiers'] / num_years).round(2)
player_summary['Qualification Rate %'] = (player_summary['Total Qualifiers'] / player_summary['Total Picks'] * 100).round(1)

print(player_summary.to_string())

# Detailed breakdown
print(f'\n=== Detailed Breakdown by Player and Tier ===')
for player in range(1, 9):
    player_picks = picks_df[picks_df['player'] == player]
    print(f'\nPlayer {player}:')
    
    for cluster in [2, 1, 0]:  # High to low
        tier_label = 'High' if cluster == 2 else 'Medium' if cluster == 1 else 'Low'
        tier_picks = player_picks[player_picks['cluster'] == cluster]
        
        if len(tier_picks) > 0:
            qualified = (tier_picks['qualified'] == 1).sum()
            total = len(tier_picks)
            avg_per_year = total / num_years
            qual_avg = qualified / num_years
            qual_rate = (qualified / total * 100) if total > 0 else 0
            
            print(f'  Tier {cluster} ({tier_label}): {qual_avg:.2f} qualifiers/year from {avg_per_year:.2f} picks/year ({qual_rate:.1f}% qual rate)')
