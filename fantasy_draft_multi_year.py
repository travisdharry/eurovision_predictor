import pandas as pd
import numpy as np

# Read the clustered data with direct qualifiers as cluster 3
df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Get all years that have both semi-finals
years_with_semis = df[df['semi_final'].astype(str).isin(['1', '2'])]['year'].unique()
years_with_semis = sorted([y for y in years_with_semis if y >= 2009])  # Modern era

print(f'=== Fantasy Draft Simulation Across Multiple Years ===')
print(f'Years to simulate: {years_with_semis}')
print(f'Total simulations: {len(years_with_semis)}')

all_results = []

for YEAR in years_with_semis:
    year_data = df[df['year'] == YEAR].copy()
    
    # Split by semi-final
    semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
    semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()
    
    # Skip if not enough entries
    if len(semi1) < 15 or len(semi2) < 16:
        print(f'Skipping {YEAR} - insufficient entries')
        continue
    
    # Sort by cluster (high to low) within each semi
    semi1 = semi1.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
    semi2 = semi2.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
    
    # Simulate draft
    semi1_draft_order = [1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1]
    semi2_draft_order = [8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]
    
    # Initialize player rosters
    player_rosters = {i: [] for i in range(1, 9)}
    
    # Semi 1 draft
    for pick_num, player in enumerate(semi1_draft_order):
        if pick_num < len(semi1):
            country = semi1.iloc[pick_num]
            player_rosters[player].append(country)
    
    # Semi 2 draft
    for pick_num, player in enumerate(semi2_draft_order):
        if pick_num < len(semi2):
            country = semi2.iloc[pick_num]
            player_rosters[player].append(country)
    
    # Calculate total points for each player
    for player in range(1, 9):
        roster = player_rosters[player]
        total_points = sum(country['final_total_points'] for country in roster)
        num_countries = len(roster)
        avg_points = total_points / num_countries if num_countries > 0 else 0
        
        all_results.append({
            'year': YEAR,
            'player': player,
            'total_points': total_points,
            'avg_points': avg_points,
            'num_countries': num_countries
        })

# Analyze results
results_df = pd.DataFrame(all_results)

print(f'\n=== OVERALL FAIRNESS ANALYSIS (All Years) ===')
print(f'Total player-years simulated: {len(results_df)}')

# Average by draft position
position_avg = results_df.groupby('player').agg({
    'total_points': 'mean',
    'avg_points': 'mean',
    'num_countries': 'mean'
}).round(1)

position_avg = position_avg.sort_values('total_points', ascending=False)
position_avg.columns = ['Avg Total Points', 'Avg Points/Country', 'Avg Countries']

print(f'\n=== Average Performance by Draft Position ===')
print(position_avg.to_string())

print(f'\n=== Fairness Metrics ===')
print(f'Standard Deviation across positions: {position_avg["Avg Total Points"].std():.1f}')
print(f'Range (best - worst): {position_avg["Avg Total Points"].max() - position_avg["Avg Total Points"].min():.1f} points')
print(f'Best average position: Player {position_avg["Avg Total Points"].idxmax():.0f} ({position_avg["Avg Total Points"].max():.1f} points)')
print(f'Worst average position: Player {position_avg["Avg Total Points"].idxmin():.0f} ({position_avg["Avg Total Points"].min():.1f} points)')

# Show year-by-year breakdown
print(f'\n=== Year-by-Year Results ===')
for year in sorted(results_df['year'].unique()):
    year_results = results_df[results_df['year'] == year].sort_values('total_points', ascending=False)
    winner = year_results.iloc[0]
    loser = year_results.iloc[-1]
    print(f'{year}: Best=Player {winner["player"]:.0f} ({winner["total_points"]:.0f}pts), Worst=Player {loser["player"]:.0f} ({loser["total_points"]:.0f}pts), Range={winner["total_points"]-loser["total_points"]:.0f}pts')

# Draft position advantages by round
print(f'\n=== Pick Position Analysis ===')
print('Player 1 picks: 1st, 16th (Semi 1), 8th, 9th (Semi 2)')
print('Player 2 picks: 2nd, 15th (Semi 1), 7th, 10th (Semi 2)')
print('Player 3 picks: 3rd, 14th (Semi 1), 6th, 11th (Semi 2)')
print('Player 4 picks: 4th, 13th (Semi 1), 5th, 12th (Semi 2)')
print('Player 5 picks: 5th, 12th (Semi 1), 4th, 13th (Semi 2)')
print('Player 6 picks: 6th, 11th (Semi 1), 3rd, 14th (Semi 2)')
print('Player 7 picks: 7th, 10th (Semi 1), 2nd, 15th (Semi 2)')
print('Player 8 picks: 8th, 9th (Semi 1), 1st, 16th (Semi 2)')
