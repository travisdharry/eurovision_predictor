import pandas as pd
import numpy as np

# Read the clustered data with direct qualifiers as cluster 3
df = pd.read_csv('data/song_data_clustered_semi_with_dq.csv')

# Pick a year to simulate - let's use 2023 (most recent complete year)
YEAR = 2023

year_data = df[df['year'] == YEAR].copy()

print(f'=== Fantasy Draft Simulation for {YEAR} ===')
print(f'Total entries: {len(year_data)}')
print(f'\nCluster distribution:')
print(year_data.groupby('cluster').size())

# Split by semi-final (handle as string since it contains '-')
semi1 = year_data[year_data['semi_final'].astype(str) == '1'].copy()
semi2 = year_data[year_data['semi_final'].astype(str) == '2'].copy()

print(f'\nSemi-Final 1 entries: {len(semi1)}')
print(f'Semi-Final 2 entries: {len(semi2)}')

# Sort by cluster (high to low) within each semi
# Players will pick best available from their preferred cluster
semi1 = semi1.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)
semi2 = semi2.sort_values(['cluster', 'semi_total_points'], ascending=[False, False]).reset_index(drop=True)

print(f'\n=== Semi-Final 1 Available (sorted by cluster, then semi_total_points) ===')
for i, row in semi1.iterrows():
    cluster_label = f"Cluster {row['cluster']}"
    print(f"{i+1:2d}. {row['country']:20s} | {cluster_label} | Semi: {row['semi_total_points']:3.0f} | Final: {row['final_total_points']:3.0f}")

print(f'\n=== Semi-Final 2 Available (sorted by cluster, then semi_total_points) ===')
for i, row in semi2.iterrows():
    cluster_label = f"Cluster {row['cluster']}"
    print(f"{i+1:2d}. {row['country']:20s} | {cluster_label} | Semi: {row['semi_total_points']:3.0f} | Final: {row['final_total_points']:3.0f}")

# Simulate draft
# Semi 1: Snake order 1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1
# Semi 2: Reverse snake 8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8

semi1_draft_order = [1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1]
semi2_draft_order = [8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]

# Initialize player rosters
player_rosters = {i: [] for i in range(1, 9)}

# Semi 1 draft (pick top 16 available)
print(f'\n=== SEMI-FINAL 1 DRAFT ===')
for pick_num, player in enumerate(semi1_draft_order):
    if pick_num < len(semi1):
        country = semi1.iloc[pick_num]
        player_rosters[player].append(country)
        print(f"Pick {pick_num+1:2d} - Player {player}: {country['country']:20s} (Cluster {country['cluster']}, Semi: {country['semi_total_points']:3.0f}, Final: {country['final_total_points']:3.0f})")
    else:
        print(f"Pick {pick_num+1:2d} - Player {player}: NO COUNTRY AVAILABLE")

# Semi 2 draft (pick top 16 available)
print(f'\n=== SEMI-FINAL 2 DRAFT ===')
for pick_num, player in enumerate(semi2_draft_order):
    if pick_num < len(semi2):
        country = semi2.iloc[pick_num]
        player_rosters[player].append(country)
        print(f"Pick {pick_num+1:2d} - Player {player}: {country['country']:20s} (Cluster {country['cluster']}, Semi: {country['semi_total_points']:3.0f}, Final: {country['final_total_points']:3.0f})")
    else:
        print(f"Pick {pick_num+1:2d} - Player {player}: NO COUNTRY AVAILABLE")

# Calculate total points for each player
print(f'\n=== FINAL RESULTS ===')
player_totals = []
for player in range(1, 9):
    roster = player_rosters[player]
    total_points = sum(country['final_total_points'] for country in roster)
    avg_points = total_points / len(roster) if roster else 0
    
    print(f'\nPlayer {player}:')
    for country in roster:
        print(f'  {country["country"]:20s} - {country["final_total_points"]:3.0f} points (Cluster {country["cluster"]})')
    print(f'  TOTAL: {total_points:.0f} points (Average: {avg_points:.1f})')
    
    player_totals.append({
        'player': player,
        'total_points': total_points,
        'avg_points': avg_points,
        'num_countries': len(roster)
    })

# Summary
print(f'\n=== FAIRNESS ANALYSIS ===')
totals_df = pd.DataFrame(player_totals)
totals_df = totals_df.sort_values('total_points', ascending=False)
print(totals_df.to_string(index=False))

print(f'\nStandard Deviation of Total Points: {totals_df["total_points"].std():.1f}')
print(f'Range: {totals_df["total_points"].max() - totals_df["total_points"].min():.0f} points')
print(f'Best Position: Player {totals_df.iloc[0]["player"]:.0f} ({totals_df.iloc[0]["total_points"]:.0f} points)')
print(f'Worst Position: Player {totals_df.iloc[-1]["player"]:.0f} ({totals_df.iloc[-1]["total_points"]:.0f} points)')
