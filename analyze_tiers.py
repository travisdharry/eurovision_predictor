import pandas as pd

df = pd.read_csv('data/song_data_clustered_semi_normalized.csv')

# Assign proxy semi scores to direct qualifiers FIRST
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

# Assign tiers based on year ranking
# Tier 1: 10 countries (direct qualifiers + top semi scores to reach 10)
# Tier 2: Next 10 highest semi scores
# Tier 3: Remaining countries
df['tier'] = 0

for year in df['year'].unique():
    year_mask = df['year'] == year
    year_data = df[year_mask].copy()
    
    # Start with direct qualifiers in Tier 1
    direct_qual_mask = year_mask & (df['direct_qualifier_10'] == 1)
    df.loc[direct_qual_mask, 'tier'] = 1
    num_tier1 = direct_qual_mask.sum()
    
    # Get non-direct qualifiers sorted by semi score
    non_dq = year_data[year_data['direct_qualifier_10'] == 0].copy()
    non_dq = non_dq.sort_values('semi_total_points', ascending=False)
    
    # Fill Tier 1 to 10 total
    tier1_needed = max(0, 10 - num_tier1)
    if tier1_needed > 0 and len(non_dq) > 0:
        tier1_adds = non_dq.iloc[:tier1_needed]
        for idx in tier1_adds.index:
            df.loc[idx, 'tier'] = 1
    
    # Next 10 = Tier 2
    tier2_start = tier1_needed
    tier2_end = tier2_start + 10
    if len(non_dq) > tier2_start:
        tier2_countries = non_dq.iloc[tier2_start:tier2_end]
        for idx in tier2_countries.index:
            df.loc[idx, 'tier'] = 2
    
    # Rest = Tier 3
    tier3_start = tier2_end
    if len(non_dq) > tier3_start:
        tier3_countries = non_dq.iloc[tier3_start:]
        for idx in tier3_countries.index:
            df.loc[idx, 'tier'] = 3

print('=== QUALIFICATION RATES BY TIER ===\n')
for tier in [1, 2, 3]:
    tier_data = df[df['tier'] == tier]
    qualifiers = tier_data[tier_data['qualified_10'] == 1]
    
    # Exclude direct qualifiers when calculating semi qualification rate
    semi_participants = tier_data[tier_data['direct_qualifier_10'] == 0]
    semi_qualifiers = semi_participants[semi_participants['qualified_10'] == 1]
    
    qual_rate = (len(qualifiers) / len(tier_data)) * 100 if len(tier_data) > 0 else 0
    semi_qual_rate = (len(semi_qualifiers) / len(semi_participants)) * 100 if len(semi_participants) > 0 else 0
    
    avg_final_score = tier_data['final_total_points'].mean()
    avg_final_score_qualifiers = qualifiers['final_total_points'].mean()
    
    print(f'Tier {tier}:')
    print(f'  Total countries: {len(tier_data)}')
    print(f'  Overall qualification rate: {qual_rate:.1f}%')
    print(f'  Semi-finalist qualification rate: {semi_qual_rate:.1f}%')
    print(f'  Average final score (all): {avg_final_score:.1f}')
    print(f'  Average final score (qualifiers): {avg_final_score_qualifiers:.1f}')
    print()
