import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Read the CSV
df = pd.read_csv('data/song_data_prepro1.csv')

print('=== Original Data Shape ===')
print(f'Total rows: {len(df)}')
print(f'\nDirect qualifier distribution:')
print(df['direct_qualifier_10'].value_counts())

# Split into semi-final participants and direct qualifiers
semi_participants = df[df['direct_qualifier_10'] == 0].copy()
direct_qualifiers = df[df['direct_qualifier_10'] == 1].copy()

print(f'\n=== Data Split ===')
print(f'Semi-final participants: {len(semi_participants)}')
print(f'Direct qualifiers: {len(direct_qualifiers)}')

# Remove rows with NaN in semi_total_points for semi participants
semi_participants = semi_participants[semi_participants['semi_total_points'].notna()]

print(f'Semi participants with valid semi_total_points: {len(semi_participants)}')

# Print stats on semi_total_points
print(f'\n=== Semi-Final Total Points Statistics ===')
print(semi_participants['semi_total_points'].describe())

# Perform K-means clustering with 3 clusters on semi-final participants only
X = semi_participants[['semi_total_points']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
semi_participants['cluster'] = kmeans.fit_predict(X)

# Sort cluster labels by mean points (0=low, 1=mid, 2=high)
cluster_means = semi_participants.groupby('cluster')['semi_total_points'].mean().sort_values()
cluster_mapping = {old: new for new, old in enumerate(cluster_means.index)}
semi_participants['cluster'] = semi_participants['cluster'].map(cluster_mapping)

# Assign all direct qualifiers to cluster 3
direct_qualifiers['cluster'] = 3

# Combine both datasets
combined_df = pd.concat([semi_participants, direct_qualifiers], ignore_index=True)

print(f'\n=== Cluster Analysis ===')

# Analyze clusters 0-2 (semi-final participants)
for i in range(3):
    cluster_data = combined_df[combined_df['cluster'] == i]
    label = 'Low' if i==0 else 'Medium' if i==1 else 'High'
    print(f'\nCluster {i} ({label} Semi Points):')
    print(f'  Count: {len(cluster_data)}')
    print(f'  Semi points range: {cluster_data["semi_total_points"].min():.0f} - {cluster_data["semi_total_points"].max():.0f}')
    print(f'  Mean semi points: {cluster_data["semi_total_points"].mean():.1f}')
    
    # Check qualification rate
    qualified = (cluster_data['qualified_10'] == 1).sum()
    qual_rate = (qualified / len(cluster_data) * 100) if len(cluster_data) > 0 else 0
    print(f'  Qualified for final: {qualified}/{len(cluster_data)} ({qual_rate:.1f}%)')
    
    # Champions in cluster
    print(f'  Champions in cluster: {cluster_data["is_champion"].sum()}')
    
    # Average final points for those who qualified
    qualified_data = cluster_data[cluster_data['qualified_10'] == 1]
    if len(qualified_data) > 0:
        avg_final = qualified_data['final_total_points'].mean()
        print(f'  Average final points (if qualified): {avg_final:.1f}')

# Analyze cluster 3 (direct qualifiers)
cluster_3_data = combined_df[combined_df['cluster'] == 3]
print(f'\nCluster 3 (Direct Qualifiers - Big 5/Host):')
print(f'  Count: {len(cluster_3_data)}')
print(f'  Final points range: {cluster_3_data["final_total_points"].min():.0f} - {cluster_3_data["final_total_points"].max():.0f}')
print(f'  Mean final points: {cluster_3_data["final_total_points"].mean():.1f}')
print(f'  Champions in cluster: {cluster_3_data["is_champion"].sum()}')

# Save clustered data
output_file = 'data/song_data_clustered_semi_with_dq.csv'
combined_df.to_csv(output_file, index=False)
print(f'\n=== Output ===')
print(f'Clustered data saved to: {output_file}')
print(f'Cluster assignments:')
print(f'  0 = Low Semi Points')
print(f'  1 = Medium Semi Points')
print(f'  2 = High Semi Points')
print(f'  3 = Direct Qualifiers')

# Average cluster counts by year
print('\n=== Average Count per Cluster by Year ===')
cluster_by_year = combined_df.groupby(['year', 'cluster']).size().unstack(fill_value=0)
avg_per_cluster = cluster_by_year.mean()
labels = ['Low', 'Medium', 'High', 'Direct Qualifiers']
for cluster in range(4):
    label = labels[cluster]
    print(f'Cluster {cluster} ({label}): {avg_per_cluster[cluster]:.2f} entries per year')
