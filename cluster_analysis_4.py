import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Read the CSV
df = pd.read_csv('data/song_data_prepro1.csv')

print('=== Original Data Shape ===')
print(f'Total rows: {len(df)}')
print(f'\nDirect qualifier distribution:')
print(df['direct_qualifier_10'].value_counts())

# NO FILTERING - use all data
filtered_df = df.copy()

print(f'\n=== Using All Data (no filtering) ===')
print(f'Total rows: {len(filtered_df)}')

# Remove rows with NaN in final_total_points
filtered_df = filtered_df[filtered_df['final_total_points'].notna()]

print(f'Rows with valid final_total_points: {len(filtered_df)}')

# Print stats on final_total_points
print(f'\n=== Final Total Points Statistics ===')
print(filtered_df['final_total_points'].describe())

# Perform K-means clustering with 4 clusters
X = filtered_df[['final_total_points']].values
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
filtered_df['cluster'] = kmeans.fit_predict(X)

# Sort cluster labels by mean points (0=lowest, 1=low-mid, 2=mid-high, 3=highest)
cluster_means = filtered_df.groupby('cluster')['final_total_points'].mean().sort_values()
cluster_mapping = {old: new for new, old in enumerate(cluster_means.index)}
filtered_df['cluster'] = filtered_df['cluster'].map(cluster_mapping)

print(f'\n=== Cluster Analysis (4 Clusters) ===')
labels = ['Very Low', 'Low', 'Medium', 'High']
for i in range(4):
    cluster_data = filtered_df[filtered_df['cluster'] == i]
    label = labels[i]
    print(f'\nCluster {i} ({label} points):')
    print(f'  Count: {len(cluster_data)}')
    print(f'  Points range: {cluster_data["final_total_points"].min():.0f} - {cluster_data["final_total_points"].max():.0f}')
    print(f'  Mean points: {cluster_data["final_total_points"].mean():.1f}')
    print(f'  Champions in cluster: {cluster_data["is_champion"].sum()}')
    print(f'  Direct qualifiers (direct_qualifier_10=1): {(cluster_data["direct_qualifier_10"] == 1).sum()}')
    
    # Show a few examples
    examples = cluster_data.nsmallest(3, 'final_total_points')[['year', 'country', 'final_total_points', 'direct_qualifier_10']]
    print(f'  Examples (lowest points):')
    for _, row in examples.iterrows():
        dq = 'DQ' if row['direct_qualifier_10'] == 1 else 'SF'
        print(f'    {int(row["year"])} {row["country"]}: {row["final_total_points"]:.0f} points ({dq})')

# Save clustered data
output_file = 'data/song_data_clustered_4.csv'
filtered_df.to_csv(output_file, index=False)
print(f'\n=== Output ===')
print(f'Clustered data saved to: {output_file}')
print(f'Added cluster column (0=Very Low, 1=Low, 2=Medium, 3=High)')

# Show cluster distribution by direct_qualifier_10
print(f'\n=== Cluster Distribution by Direct Qualifier Status ===')
crosstab = pd.crosstab(filtered_df['cluster'], filtered_df['direct_qualifier_10'], margins=True)
print(crosstab)

# Average cluster counts by year
print('\n=== Average Count per Cluster by Year ===')
cluster_by_year = filtered_df.groupby(['year', 'cluster']).size().unstack(fill_value=0)
avg_per_cluster = cluster_by_year.mean()
for cluster in range(4):
    label = labels[cluster]
    print(f'Cluster {cluster} ({label}): {avg_per_cluster[cluster]:.2f} entries per year')
