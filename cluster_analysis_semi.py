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

# Remove rows with NaN in semi_total_points
filtered_df = filtered_df[filtered_df['semi_total_points'].notna()]

print(f'Rows with valid semi_total_points: {len(filtered_df)}')

# Print stats on semi_total_points
print(f'\n=== Semi-Final Total Points Statistics ===')
print(filtered_df['semi_total_points'].describe())

# Perform K-means clustering with 3 clusters
X = filtered_df[['semi_total_points']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
filtered_df['cluster'] = kmeans.fit_predict(X)

# Sort cluster labels by mean points (0=low, 1=mid, 2=high)
cluster_means = filtered_df.groupby('cluster')['semi_total_points'].mean().sort_values()
cluster_mapping = {old: new for new, old in enumerate(cluster_means.index)}
filtered_df['cluster'] = filtered_df['cluster'].map(cluster_mapping)

print(f'\n=== Cluster Analysis ===')
for i in range(3):
    cluster_data = filtered_df[filtered_df['cluster'] == i]
    label = 'Low' if i==0 else 'Medium' if i==1 else 'High'
    print(f'\nCluster {i} ({label} points):')
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
    
    # Show a few examples
    examples = cluster_data.nsmallest(3, 'semi_total_points')[['year', 'country', 'semi_total_points', 'qualified_10', 'final_total_points']]
    print(f'  Examples (lowest semi points):')
    for _, row in examples.iterrows():
        qual_status = 'Qualified' if row['qualified_10'] == 1 else 'Not qualified'
        final_pts = f"{row['final_total_points']:.0f}" if pd.notna(row['final_total_points']) else "N/A"
        print(f'    {int(row["year"])} {row["country"]}: {row["semi_total_points"]:.0f} semi pts ({qual_status}, Final: {final_pts})')

# Save clustered data
output_file = 'data/song_data_clustered_semi.csv'
filtered_df.to_csv(output_file, index=False)
print(f'\n=== Output ===')
print(f'Clustered data saved to: {output_file}')
print(f'Added cluster column (0=Low, 1=Medium, 2=High)')

# Average cluster counts by year
print('\n=== Average Count per Cluster by Year ===')
cluster_by_year = filtered_df.groupby(['year', 'cluster']).size().unstack(fill_value=0)
avg_per_cluster = cluster_by_year.mean()
for cluster in [0, 1, 2]:
    label = 'Low' if cluster==0 else 'Medium' if cluster==1 else 'High'
    print(f'Cluster {cluster} ({label}): {avg_per_cluster[cluster]:.2f} entries per year')
