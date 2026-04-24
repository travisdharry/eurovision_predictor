import pandas as pd

df = pd.read_csv('data/song_data_clustered_all.csv')

# Filter for direct qualifiers in top tier (cluster 2)
top_tier_dq = df[(df['direct_qualifier_10'] == 1) & (df['cluster'] == 2)]

print('=== Direct Qualifiers in Top Tier (Cluster 2) ===')
print(f'Count: {len(top_tier_dq)}')
print(f'Average final_total_points: {top_tier_dq["final_total_points"].mean():.1f}')
print(f'Median final_total_points: {top_tier_dq["final_total_points"].median():.1f}')
print(f'Min: {top_tier_dq["final_total_points"].min():.0f}')
print(f'Max: {top_tier_dq["final_total_points"].max():.0f}')

print(f'\n=== All Direct Qualifiers in Top Tier ===')
for _, row in top_tier_dq.sort_values('final_total_points', ascending=False).iterrows():
    champ = 'CHAMPION' if row['is_champion'] == 1 else '        '
    print(f'{champ} {int(row["year"])} {row["country"]}: {row["final_total_points"]:.0f} points')

print(f'\n=== Comparison: All Top Tier (Cluster 2) ===')
all_top_tier = df[df['cluster'] == 2]
print(f'All entries in top tier: {len(all_top_tier)}')
print(f'Average final_total_points (all): {all_top_tier["final_total_points"].mean():.1f}')
print(f'Direct qualifiers: {len(top_tier_dq)} ({len(top_tier_dq)/len(all_top_tier)*100:.1f}%)')
print(f'Semi-final qualifiers: {len(all_top_tier) - len(top_tier_dq)} ({(len(all_top_tier) - len(top_tier_dq))/len(all_top_tier)*100:.1f}%)')
