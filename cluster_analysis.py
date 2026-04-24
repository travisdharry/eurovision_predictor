import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Read the CSV
df = pd.read_csv('data/song_data_prepro1.csv')

print('=== Original Data Shape ===')
print(f'Total rows: {len(df)}')
print(f'\nDirect qualifier distribution:')
print(df['direct_qualifier_10'].value_counts())

# Filter where direct_qualifier_10 = 0
filtered_df = df[df['direct_qualifier_10'] == 0].copy()

print(f'\n=== After Filtering (direct_qualifier_10 = 0) ===')
print(f'Filtered rows: {len(filtered_df)}')

# Remove rows with NaN in final_total_points
filtered_df = filtered_df[filtered_df['final_total_points'].notna()]

print(f'Rows with valid final_total_points: {len(filtered_df)}')

# Print stats on final_total_points
print(f'\n=== Final Total Points Statistics ===')
print(filtered_df['final_total_points'].describe())

# Perform K-means clustering with 3 clusters
X = filtered_df[['final_total_points']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
filtered_df['cluster'] = kmeans.fit_predict(X)

# Sort cluster labels by mean points (0=low, 1=mid, 2=high)
cluster_means = filtered_df.groupby('cluster')['final_total_points'].mean().sort_values()
cluster_mapping = {old: new for new, old in enumerate(cluster_means.index)}
filtered_df['cluster'] = filtered_df['cluster'].map(cluster_mapping)

print(f'\n=== Cluster Analysis ===')
for i in range(3):
    cluster_data = filtered_df[filtered_df['cluster'] == i]
    label = 'Low' if i==0 else 'Medium' if i==1 else 'High'
    print(f'\nCluster {i} ({label} points):')
    print(f'  Count: {len(cluster_data)}')
    print(f'  Points range: {cluster_data["final_total_points"].min():.0f} - {cluster_data["final_total_points"].max():.0f}')
    print(f'  Mean points: {cluster_data["final_total_points"].mean():.1f}')
    print(f'  Champions in cluster: {cluster_data["is_champion"].sum()}')
    
    # Show a few examples
    examples = cluster_data.nsmallest(3, 'final_total_points')[['year', 'country', 'final_total_points']]
    print(f'  Examples (lowest points):')
    for _, row in examples.iterrows():
        print(f'    {int(row["year"])} {row["country"]}: {row["final_total_points"]:.0f} points')

# Save clustered data
output_file = 'data/song_data_clustered.csv'
filtered_df.to_csv(output_file, index=False)
print(f'\n=== Output ===')
print(f'Clustered data saved to: {output_file}')
print(f'Added cluster column (0=Low, 1=Medium, 2=High)')
