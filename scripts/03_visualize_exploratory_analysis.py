import os

import matplotlib.pyplot as plt
import pandas as pd

from simulation_utils import assign_tiers

# Ensure outputs directory exists
os.makedirs('outputs', exist_ok=True)

# Load and tier data (same tier settings as exploratory analysis)
df = pd.read_csv('data/song_data_balanced.csv')
df = assign_tiers(df, tier1_size=10, tier2_size=10)

# Build tier summary for scatter plot
tier_summary_rows = []
for tier in [1, 2, 3]:
    tier_data = df[df['tier'] == tier]
    qualifiers = tier_data[tier_data['qualified_10'] == 1]

    overall_qual_rate = (len(qualifiers) / len(tier_data)) * 100 if len(tier_data) > 0 else 0
    avg_final_score_qualifiers = qualifiers['final_total_points'].mean()

    tier_summary_rows.append(
        {
            'tier': tier,
            'overall_qualification_rate': overall_qual_rate,
            'avg_final_score_qualifiers': avg_final_score_qualifiers,
        }
    )

tier_summary = pd.DataFrame(tier_summary_rows)

# Build finishing-place summary for bar chart
finalists = df[(df['qualified_10'] == 1) | (df['direct_qualifier_10'] == 1)].copy()
finalists['finishing_place'] = (
    finalists.groupby('year')['final_total_points']
    .rank(method='first', ascending=False)
    .astype(int)
)

finishing_place_avg = (
    finalists.groupby('finishing_place')['final_total_points']
    .mean()
    .reset_index()
    .sort_values('finishing_place')
)

# Create figure
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('Exploratory Analysis: Tier Performance and Final Placement Scoring', fontsize=14, fontweight='bold')

# Plot 1: Tier scatter plot
ax1 = axes[0]
colors = {1: '#2E8B57', 2: '#1f77b4', 3: '#d62728'}

for _, row in tier_summary.iterrows():
    tier = int(row['tier'])
    x = row['overall_qualification_rate']
    y = row['avg_final_score_qualifiers']
    ax1.scatter(x, y, s=180, color=colors[tier], alpha=0.85, edgecolor='black', linewidth=0.7)
    ax1.annotate(f'Tier {tier}', (x, y), xytext=(6, 6), textcoords='offset points', fontsize=10, fontweight='bold')

ax1.set_title('Tiers: Qualification Rate vs Avg Final Score (Qualifiers)', fontsize=11, fontweight='bold')
ax1.set_xlabel('Overall qualification rate (%)')
ax1.set_ylabel('Average final score (qualifiers)')
ax1.set_xlim(left=0)
ax1.set_ylim(bottom=0)
ax1.grid(True, alpha=0.25)

# Plot 2: Bar chart by finishing place
ax2 = axes[1]
ax2.bar(
    finishing_place_avg['finishing_place'],
    finishing_place_avg['final_total_points'],
    color='#6A5ACD',
    alpha=0.85,
)
ax2.set_title('Average Final Score (Qualifiers) by Finishing Place', fontsize=11, fontweight='bold')
ax2.set_xlabel('Finishing place')
ax2.set_ylabel('Average final score')
ax2.set_xlim(left=0)
ax2.set_ylim(bottom=0)
ax2.grid(True, axis='y', alpha=0.25)

# Keep x-axis readable for many places
max_place = int(finishing_place_avg['finishing_place'].max())
step = 2 if max_place > 20 else 1
ax2.set_xticks(list(range(1, max_place + 1, step)))

plt.tight_layout(rect=[0, 0, 1, 0.95])

output_path = 'outputs/exploratory_analysis_visualization.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f'Visualization saved to: {output_path}')

# Create a second output with only the left chart and minimal styling
fig_left, ax_left = plt.subplots(1, 1, figsize=(8, 7))

for _, row in tier_summary.iterrows():
    tier = int(row['tier'])
    x = row['overall_qualification_rate']
    y = row['avg_final_score_qualifiers']
    ax_left.scatter(x, y, s=180, color=colors[tier], alpha=0.85, edgecolor='black', linewidth=0.7)
    ax_left.annotate(f'Tier {tier}', (x, y), xytext=(6, 6), textcoords='offset points', fontsize=10, fontweight='bold')

ax_left.set_xlabel('Overall qualification rate (%)')
ax_left.set_ylabel('Average final score (qualifiers)')
ax_left.set_xlim(left=0)
ax_left.set_ylim(bottom=0)

# Remove grid lines
ax_left.grid(False)

# Keep axes visible (left/bottom), hide only top/right borders
ax_left.spines['top'].set_visible(False)
ax_left.spines['right'].set_visible(False)

# Set y-axis to 0-250 with labels every 50, excluding 0
ax_left.set_ylim(0, 250)
ax_left.set_yticks([50, 100, 150, 200, 250])

# Keep default tick marks

left_only_output_path = 'outputs/exploratory_analysis_left_chart_only.png'
fig_left.tight_layout()
fig_left.savefig(left_only_output_path, dpi=300, bbox_inches='tight')
print(f'Left chart only visualization saved to: {left_only_output_path}')

plt.show()
