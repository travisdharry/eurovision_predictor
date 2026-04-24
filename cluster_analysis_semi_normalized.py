import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Read the preprocessed data
df = pd.read_csv('data/song_data_prepro1.csv')

print('=== Clustering Eurovision Semi-Final Performance (Normalized Within Year) ===\n')

# Filter to only semi-final participants (not direct qualifiers)
# Also filter out entries with missing semi_total_points
semi_participants = df[
    (df['direct_qualifier_10'] == 0) & 
    (df['semi_total_points'].notna())
].copy()

print(f'Total entries: {len(df)}')
print(f'Semi-final participants: {len(semi_participants)}')
print(f'Direct qualifiers: {len(df[df["direct_qualifier_10"] == 1])}')
print(f'Entries with missing semi scores: {len(df[(df["direct_qualifier_10"] == 0) & (df["semi_total_points"].isna())])}\n')

# Normalize semi_total_points within each year using z-score normalization
# (subtract mean, divide by std dev)
semi_participants['semi_total_normalized'] = 0.0

for year in semi_participants['year'].unique():
    year_mask = semi_participants['year'] == year
    year_scores = semi_participants.loc[year_mask, 'semi_total_points']
    
    # Z-score normalization: (x - mean) / std
    mean_score = year_scores.mean()
    std_score = year_scores.std()
    
    if std_score > 0:  # Avoid division by zero
        normalized = (year_scores - mean_score) / std_score
        semi_participants.loc[year_mask, 'semi_total_normalized'] = normalized
        print(f'{year}: mean={mean_score:.1f}, std={std_score:.1f}, '
              f'range=({year_scores.min():.0f} to {year_scores.max():.0f})')
    else:
        # If all scores are the same (unlikely), set to 0
        semi_participants.loc[year_mask, 'semi_total_normalized'] = 0

print(f'\nNormalized scores range: {semi_participants["semi_total_normalized"].min():.2f} to {semi_participants["semi_total_normalized"].max():.2f}')

# Perform K-means clustering on normalized scores
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

# Reshape for sklearn
X = semi_participants[['semi_total_normalized']].values
semi_participants['cluster'] = kmeans.fit_predict(X)

# Sort clusters by mean normalized score (low to high = 0, 1, 2)
cluster_means = semi_participants.groupby('cluster')['semi_total_normalized'].mean().sort_values()
cluster_mapping = {old: new for new, old in enumerate(cluster_means.index)}
semi_participants['cluster'] = semi_participants['cluster'].map(cluster_mapping)

print(f'\n=== Cluster Analysis (Based on Normalized Semi-Final Scores) ===\n')

for cluster_id in range(n_clusters):
    cluster_data = semi_participants[semi_participants['cluster'] == cluster_id]
    
    # Calculate statistics on NORMALIZED scores
    mean_norm = cluster_data['semi_total_normalized'].mean()
    min_norm = cluster_data['semi_total_normalized'].min()
    max_norm = cluster_data['semi_total_normalized'].max()
    
    # Also show original score ranges for reference
    mean_orig = cluster_data['semi_total_points'].mean()
    min_orig = cluster_data['semi_total_points'].min()
    max_orig = cluster_data['semi_total_points'].max()
    
    qualified = cluster_data['qualified_10'].sum()
    total = len(cluster_data)
    qual_rate = (qualified / total * 100) if total > 0 else 0
    
    print(f'Cluster {cluster_id}:')
    print(f'  Count: {total}')
    print(f'  Normalized score: {mean_norm:.2f} (range: {min_norm:.2f} to {max_norm:.2f})')
    print(f'  Original score: {mean_orig:.1f} (range: {min_orig:.0f} to {max_orig:.0f})')
    print(f'  Qualification rate: {qual_rate:.1f}% ({qualified}/{total})')
    print()

# Add direct qualifiers as cluster 3
direct_qualifiers = df[df['direct_qualifier_10'] == 1].copy()
direct_qualifiers['cluster'] = 3
direct_qualifiers['semi_total_normalized'] = np.nan  # No normalized score for DQs

# Combine semi participants and direct qualifiers
df_clustered = pd.concat([semi_participants, direct_qualifiers], ignore_index=True)

print(f'Total clustered entries: {len(df_clustered)}')
print(f'  Cluster 0 (Low): {len(df_clustered[df_clustered["cluster"] == 0])}')
print(f'  Cluster 1 (Medium): {len(df_clustered[df_clustered["cluster"] == 1])}')
print(f'  Cluster 2 (High): {len(df_clustered[df_clustered["cluster"] == 2])}')
print(f'  Cluster 3 (Direct Qualifiers): {len(df_clustered[df_clustered["cluster"] == 3])}')

# Save to CSV
output_file = 'data/song_data_clustered_semi_normalized.csv'
df_clustered.to_csv(output_file, index=False)
print(f'\nClustered data saved to: {output_file}')

# Show sample entries from each cluster
print('\n=== Sample Entries by Cluster ===\n')
for cluster_id in range(4):
    cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
    print(f'Cluster {cluster_id} sample:')
    sample = cluster_data[['year', 'country', 'semi_total_points', 'semi_total_normalized', 
                           'final_total_points', 'qualified_10']].head(3)
    print(sample.to_string(index=False))
    print()
