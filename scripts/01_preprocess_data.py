import pandas as pd
import numpy as np

# Read the original preprocessed data
df = pd.read_csv('data/song_data_manual_preprocessing.csv')

print('=== Eurovision Data Preprocessing: Balancing Direct Qualifiers ===\n')
print(f'Total entries: {len(df)}')
print(f'Semi-final participants: {len(df[df["direct_qualifier_10"] == 0])}')
print(f'Direct qualifiers: {len(df[df["direct_qualifier_10"] == 1])}\n')

# Set random seed for reproducibility
np.random.seed(42)

# For each year, split direct qualifiers 50/50 between semi-finals
for year in df['year'].unique():
    year_mask = df['year'] == year
    dq_mask = year_mask & (df['direct_qualifier_10'] == 1)
    
    if dq_mask.sum() > 0:
        # Get indices of direct qualifiers for this year
        dq_indices = df[dq_mask].index.tolist()
        
        # Shuffle and split 50/50
        np.random.shuffle(dq_indices)
        split_point = len(dq_indices) // 2
        
        semi1_indices = dq_indices[:split_point]
        semi2_indices = dq_indices[split_point:]
        
        # Assign to semi-finals
        df.loc[semi1_indices, 'semi_final'] = 1
        df.loc[semi2_indices, 'semi_final'] = 2
        
        print(f'{year}: {len(dq_indices)} DQs split into Semi 1 ({len(semi1_indices)}) and Semi 2 ({len(semi2_indices)})')

# Verify the split
print('\n=== Verification ===')
dq_df = df[df['direct_qualifier_10'] == 1]
print(f'Total direct qualifiers: {len(dq_df)}')
print(f'Assigned to Semi 1: {len(dq_df[dq_df["semi_final"] == 1])}')
print(f'Assigned to Semi 2: {len(dq_df[dq_df["semi_final"] == 2])}')
print(f'Unassigned: {len(dq_df[(dq_df["semi_final"] != 1) & (dq_df["semi_final"] != 2)])}')

# Assign proxy semi scores to direct qualifiers
# DQs don't have semi_total_points, so we assign them the median of top 10 semi performers
print('\n=== Assigning Proxy Semi Scores to Direct Qualifiers ===')
for year in df['year'].unique():
    year_mask = df['year'] == year
    
    # Get top 10 semi scores from non-direct qualifiers
    semi_mask = year_mask & (df['direct_qualifier_10'] == 0) & (df['semi_total_points'].notna())
    if semi_mask.any():
        top_semi_scores = df.loc[semi_mask, 'semi_total_points'].nlargest(10)
        proxy_score = top_semi_scores.median()
        
        # Assign to direct qualifiers in this year
        dq_mask = year_mask & (df['semi_total_points'].isna())
        df.loc[dq_mask, 'semi_total_points'] = proxy_score
        
        num_dqs = dq_mask.sum()
        if num_dqs > 0:
            print(f'  {year}: {num_dqs} DQs assigned proxy score {proxy_score:.0f} (median of top 10)')

# Verify all countries have semi scores
remaining_nans = df['semi_total_points'].isna().sum()
if remaining_nans > 0:
    print(f'\nWARNING: {remaining_nans} countries still missing semi_total_points!')
else:
    print(f'\n✓ All {len(df)} countries now have semi_total_points')

# Save to new file
output_file = 'data/song_data_balanced.csv'
df.to_csv(output_file, index=False)
print(f'\nBalanced data saved to: {output_file}')
print('✓ Direct qualifiers evenly distributed between semi-final pools')
print('✓ Proxy semi scores assigned to all direct qualifiers')
