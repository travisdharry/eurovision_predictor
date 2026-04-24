import pandas as pd
import numpy as np

# Read the clustered data with direct qualifiers as cluster 3
df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Get all years that have both semi-finals
years_with_semis = df[df['semi_final'].astype(str).isin(['1', '2'])]['year'].unique()
years_with_semis = sorted([y for y in years_with_semis if y >= 2009])  # Modern era

print(f'=== Fantasy Draft Token System Analysis ===')
print(f'Gold Token: Tier 0 country that qualified')
print(f'Silver Token: Tier 1 country that qualified')
print(f'Bronze Token: Tier 2 country (all qualify)')
print(f'No tokens for Tier 3 (direct qualifiers)\n')

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
    
    # Define player strategies
    # Players 1, 2, 7, 8: Seek highest tier (safe picks)
    # Players 3, 4, 5, 6: Seek tokens (risky picks - go for gold/silver/bronze)
    token_seekers = {3, 4, 5, 6}
    
    def pick_country(available_pool, player):
        """Pick best country from available pool based on player strategy"""
        if player in token_seekers:
            # Token strategy: prioritize low tiers (potential for gold/silver tokens)
            # Sort by cluster ascending (0, 1, 2), then by semi_total_points descending within tier
            return available_pool.sort_values(['cluster', 'semi_total_points'], 
                                             ascending=[True, False]).iloc[0]
        else:
            # Safe strategy: prioritize high tiers (guaranteed qualifiers)
            # Sort by cluster descending (2, 1, 0), then by semi_total_points descending within tier
            return available_pool.sort_values(['cluster', 'semi_total_points'], 
                                             ascending=[False, False]).iloc[0]
    
    # Semi 1 draft
    semi1_available = semi1.copy()
    for player in semi1_draft_order:
        if len(semi1_available) > 0:
            country = pick_country(semi1_available, player)
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
            country = pick_country(semi2_available, player)
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
        total_points = sum(country['final_total_points'] for country in roster)
        num_countries = len(roster)
        
        all_results.append({
            'year': YEAR,
            'player': player,
            'total_points': total_points,
            'num_countries': num_countries,
            'gold_tokens': player_tokens[player]['gold'],
            'silver_tokens': player_tokens[player]['silver'],
            'bronze_tokens': player_tokens[player]['bronze']
        })

# Analyze results
results_df = pd.DataFrame(all_results)

print(f'Years simulated: {len(years_with_semis) - 1}')
print(f'Total player-years: {len(results_df)}\n')

# Average by draft position
position_summary = results_df.groupby('player').agg({
    'total_points': 'mean',
    'gold_tokens': 'mean',
    'silver_tokens': 'mean',
    'bronze_tokens': 'mean'
}).round(2)

position_summary.columns = ['Avg Final Points', 'Avg Gold', 'Avg Silver', 'Avg Bronze']

# Add token points (Gold=200, Silver=100, Bronze=50)
position_summary['Gold Points'] = (position_summary['Avg Gold'] * 200).round(1)
position_summary['Silver Points'] = (position_summary['Avg Silver'] * 100).round(1)
position_summary['Bronze Points'] = (position_summary['Avg Bronze'] * 50).round(1)
position_summary['Total Token Points'] = (
    position_summary['Gold Points'] + 
    position_summary['Silver Points'] + 
    position_summary['Bronze Points']
).round(1)

# Add combined total (actual points + token points)
position_summary['Total Points'] = (position_summary['Avg Final Points'] + position_summary['Total Token Points']).round(1)

# Sort by combined total
position_summary = position_summary.sort_values('Total Points', ascending=False)

print('=== Summary by Draft Position (Combined Scoring) ===')
print('Gold = 200 pts, Silver = 100 pts, Bronze = 50 pts')
print('Total Points = Actual Final Points + Token Points')
print('Players 1,2,7,8 use safe strategy | Players 3,4,5,6 use token strategy\n')

# Show main summary
summary_display = position_summary[['Avg Final Points', 'Total Token Points', 'Total Points', 'Avg Gold', 'Avg Silver', 'Avg Bronze']]
print(summary_display.to_string())

print('\n=== Token Points Breakdown ===')
token_breakdown = position_summary[['Gold Points', 'Silver Points', 'Bronze Points', 'Total Token Points']]
print(token_breakdown.to_string())

print('\n=== Token Distribution Analysis ===')
# Show which positions excel at which token types
print('\nBest at Gold Tokens (Tier 0 qualifiers - 200 pts each):')
gold_sorted = position_summary.sort_values('Avg Gold', ascending=False).head(3)
for idx, row in gold_sorted.iterrows():
    print(f'  Player {idx}: {row["Avg Gold"]:.2f} gold tokens/year = {row["Gold Points"]:.1f} points')

print('\nBest at Silver Tokens (Tier 1 qualifiers - 100 pts each):')
silver_sorted = position_summary.sort_values('Avg Silver', ascending=False).head(3)
for idx, row in silver_sorted.iterrows():
    print(f'  Player {idx}: {row["Avg Silver"]:.2f} silver tokens/year = {row["Silver Points"]:.1f} points')

print('\nBest at Bronze Tokens (Tier 2 picks - 50 pts each):')
bronze_sorted = position_summary.sort_values('Avg Bronze', ascending=False).head(3)
for idx, row in bronze_sorted.iterrows():
    print(f'  Player {idx}: {row["Avg Bronze"]:.2f} bronze tokens/year = {row["Bronze Points"]:.1f} points')

print('\n=== Score Breakdown ===')
print('How Final Points + Token Points combine:\n')

comparison = pd.DataFrame({
    'Player': position_summary.index.tolist(),
    'Actual Points': position_summary['Avg Final Points'].values.round(1),
    'Token Points': position_summary['Total Token Points'].values,
    'Total Points': position_summary['Total Points'].values
})
comparison = comparison.sort_values('Total Points', ascending=False)
print(comparison.to_string(index=False))

print('\n=== Rankings Comparison ===')
actual_ranks = position_summary.sort_values('Avg Final Points', ascending=False).index.tolist()
total_ranks = position_summary.sort_values('Total Points', ascending=False).index.tolist()

print('Rank by Actual Points vs Total Points (Actual + Tokens):')
for i in range(8):
    actual_player = actual_ranks[i]
    total_player = total_ranks[i]
    actual_pts = position_summary.loc[actual_player, 'Avg Final Points']
    total_pts = position_summary.loc[total_player, 'Total Points']
    print(f'  #{i+1}: Player {actual_player} ({actual_pts:.1f} actual) | Player {total_player} ({total_pts:.1f} total)')

# Correlation between actual points and token points
print(f'\nCorrelation between Actual Points and Token Points:')
corr = position_summary['Avg Final Points'].corr(position_summary['Total Token Points'])
print(f'  r = {corr:.3f}')

if corr > 0.9:
    print('  Strong positive correlation - token system tracks real performance well!')
elif corr > 0.7:
    print('  Good correlation - token system reasonably reflects real performance')
else:
    print('  Weak correlation - token system does not match real performance well')
