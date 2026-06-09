import matplotlib.pyplot as plt
import numpy as np
import json

# Load Monte Carlo results
with open('outputs/gameplay_version_a.json', 'r') as f:
    version_a = json.load(f)

with open('outputs/gameplay_version_b.json', 'r') as f:
    version_b = json.load(f)

with open('outputs/gameplay_version_c.json', 'r') as f:
    version_c = json.load(f)

# Extract data
versions = ['Version A:\nBaseline\n(No Mechanics)', 
          'Version B:\nBonuses Only', 
          'Version C:\nFull System\n(Bonuses+Penalties)']
version_stage_labels = ['Draft only', 'Bonus w/o penalties', 'Bonus with penalties']
version_stage_labels_two = ['Draft only', 'Draft with tokens']

std_devs = [version_a['std_dev'], version_b['std_dev'], version_c['std_dev']]
ranges = [version_a['range'], version_b['range'], version_c['range']]
std_devs_two = [version_a['std_dev'], version_c['std_dev']]

version_a_scores = version_a['position_means']
version_b_scores = version_b['position_means']
version_c_scores = version_c['position_means']

draft_positions = list(range(1, 9))

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Eurovision Fantasy League: Gameplay Version Comparison\n(Monte Carlo: 100 iterations with randomized strategies)', 
             fontsize=15, fontweight='bold', y=0.995)

# 1. Balance Metric Journey (Std Dev)
ax1 = axes[0, 0]
ax1.plot(range(2), std_devs_two, marker='o', linewidth=3, markersize=10, color='#2E86AB')
ax1.set_ylabel('Standard Deviation (points)', fontsize=11, fontweight='bold')
ax1.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax1.set_xticks(range(2))
ax1.set_xticklabels(version_stage_labels_two)
ax1.set_title('Balance Dramatically Improves', fontsize=12, fontweight='bold')
ax1.set_ylim(bottom=0)
ax1.grid(False)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Annotate improvements
ax1.annotate('DRAMATIC IMPROVEMENT!', 
             xy=(1, std_devs_two[1]), xytext=(1.15, max(std_devs_two) * 0.9),
             arrowprops=dict(arrowstyle='->', lw=2, color='green'),
             fontsize=10, color='green', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7))

# 2. Score Distribution by Version (Box Plots)
ax2 = axes[0, 1]
box_data = [version_a_scores, version_b_scores, version_c_scores]
bp = ax2.boxplot(box_data, tick_labels=['Version A', 'Version B', 'Version C'],
                  patch_artist=True, widths=0.6)

# Color the boxes
colors = ['#E63946', '#F77F00', '#06A77D']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax2.set_ylabel('Average Score by Position (points)', fontsize=11, fontweight='bold')
ax2.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax2.set_title('Score Distribution Compression', fontsize=12, fontweight='bold')
ax2.set_ylim(bottom=0)
ax2.grid(True, alpha=0.3, axis='y')

# 3. Draft Position Score Trajectories
ax3 = axes[1, 0]
x_pos = [0, 1, 2]
x_pos_two = [0, 1]

draft_labels = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th']

for i in range(8):
    scores = [version_a_scores[i], version_c_scores[i]]
    ax3.plot(x_pos_two, scores, marker='o', label=f'{draft_labels[i]} pick', 
             linewidth=2, markersize=6, alpha=0.8)

ax3.set_ylabel('Average Score (points)', fontsize=11, fontweight='bold')
ax3.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax3.set_xticks(x_pos_two)
ax3.set_xticklabels(version_stage_labels_two)
ax3.set_title('Draft Position Advantage Elimination', fontsize=12, fontweight='bold')
ax3.legend(loc='best', ncol=2, fontsize=8, framealpha=0.9)
ax3.set_ylim(bottom=0)
ax3.grid(False)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

# 4. Strategy Performance Distribution
ax4 = axes[1, 1]

# Prepare strategy score data
strategy_box_data = []
strategy_labels = []
strategy_colors = []

# Version A - All tier1
strategy_box_data.append(version_a['strategy_scores']['tier1'])
strategy_labels.append('Version A')
strategy_colors.append('#E63946')

# Version B - Tier 1, 2, 3
for tier in ['tier1', 'tier2', 'tier3']:
    if tier in version_b['strategy_scores']:
        strategy_box_data.append(version_b['strategy_scores'][tier])
        strategy_labels.append(f'VB T{tier[-1]}')
        strategy_colors.append('#F77F00')

# Version C - Tier 1, 2, 3
for tier in ['tier1', 'tier2', 'tier3']:
    if tier in version_c['strategy_scores']:
        strategy_box_data.append(version_c['strategy_scores'][tier])
        strategy_labels.append(f'VC T{tier[-1]}')
        strategy_colors.append('#06A77D')

bp2 = ax4.boxplot(strategy_box_data, tick_labels=strategy_labels,
                   patch_artist=True, widths=0.6)

# Color the boxes by stage
for patch, color in zip(bp2['boxes'], strategy_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax4.set_ylabel('Average Score by Strategy (points)', fontsize=11, fontweight='bold')
ax4.set_xlabel('Version and Strategy', fontsize=11, fontweight='bold')
ax4.set_title('Strategy Overlap Reduction', fontsize=12, fontweight='bold')
ax4.set_ylim(bottom=0)
ax4.grid(True, alpha=0.3, axis='y')
ax4.tick_labels = ax4.get_xticklabels()
plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('outputs/gameplay_version_comparison.png', dpi=300, bbox_inches='tight')
print('Gameplay version comparison saved to outputs/gameplay_version_comparison.png')

# Additional visualization 1: left-top chart only
fig_balance, ax_balance = plt.subplots(1, 1, figsize=(8, 6))
ax_balance.plot(range(2), std_devs_two, marker='o', linewidth=3, markersize=10, color='#2E86AB')
ax_balance.set_ylabel('Standard Deviation (points)', fontsize=11, fontweight='bold')
ax_balance.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax_balance.set_xticks(range(2))
ax_balance.set_xticklabels(version_stage_labels_two)
ax_balance.set_title('Token systems make for a fairer game', fontsize=12, fontweight='bold')
ax_balance.set_ylim(bottom=0)
ax_balance.grid(False)
ax_balance.spines['top'].set_visible(False)
ax_balance.spines['right'].set_visible(False)
fig_balance.tight_layout()
fig_balance.savefig('outputs/gameplay_balance_metric_journey.png', dpi=300, bbox_inches='tight')
print('Balance metric journey saved to outputs/gameplay_balance_metric_journey.png')

# Additional visualization 2: left-bottom chart only
fig_trajectories, ax_trajectories = plt.subplots(1, 1, figsize=(8, 6))
for i in range(8):
    scores = [version_a_scores[i], version_c_scores[i]]
    ax_trajectories.plot(x_pos_two, scores, marker='o', label=f'{draft_labels[i]} pick',
                         linewidth=2, markersize=6, alpha=0.8)

ax_trajectories.set_ylabel('Average Score (points)', fontsize=11, fontweight='bold')
ax_trajectories.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax_trajectories.set_xticks(x_pos_two)
ax_trajectories.set_xticklabels(version_stage_labels_two)
ax_trajectories.set_title('Draft position no longer dictates the winner', fontsize=12, fontweight='bold')
ax_trajectories.set_ylim(bottom=0)
ax_trajectories.legend(loc='best', ncol=2, fontsize=8, framealpha=0.9)
ax_trajectories.grid(False)
ax_trajectories.spines['top'].set_visible(False)
ax_trajectories.spines['right'].set_visible(False)
fig_trajectories.tight_layout()
fig_trajectories.savefig('outputs/gameplay_draft_position_trajectories.png', dpi=300, bbox_inches='tight')
print('Draft position trajectories saved to outputs/gameplay_draft_position_trajectories.png')

# Additional visualization 3: combined simplified left-side charts (no figure title)
fig_combined, (ax_combined_left, ax_combined_right) = plt.subplots(1, 2, figsize=(14, 6))

# Combined left panel: balance metric journey
ax_combined_left.plot(range(2), std_devs_two, marker='o', linewidth=3, markersize=10, color='#2E86AB')
ax_combined_left.set_ylabel('Standard Deviation (points)', fontsize=11, fontweight='bold')
ax_combined_left.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax_combined_left.set_title('Token systems make for a fairer game', fontsize=12, fontweight='bold')
ax_combined_left.set_xticks(range(2))
ax_combined_left.set_xticklabels(version_stage_labels_two)
ax_combined_left.set_ylim(bottom=0)
ax_combined_left.grid(False)
ax_combined_left.spines['top'].set_visible(False)
ax_combined_left.spines['right'].set_visible(False)

# Combined right panel: draft position trajectories
for i in range(8):
    scores = [version_a_scores[i], version_c_scores[i]]
    ax_combined_right.plot(x_pos_two, scores, marker='o', label=f'{draft_labels[i]} pick',
                           linewidth=2, markersize=6, alpha=0.8)

ax_combined_right.set_ylabel('Average Score (points)', fontsize=11, fontweight='bold')
ax_combined_right.set_xlabel('Gameplay Version', fontsize=11, fontweight='bold')
ax_combined_right.set_title('Draft position no longer dictates the winner', fontsize=12, fontweight='bold')
ax_combined_right.set_xticks(x_pos_two)
ax_combined_right.set_xticklabels(version_stage_labels_two)
ax_combined_right.set_ylim(bottom=0)
ax_combined_right.legend(loc='best', ncol=2, fontsize=8, framealpha=0.9)
ax_combined_right.grid(False)
ax_combined_right.spines['top'].set_visible(False)
ax_combined_right.spines['right'].set_visible(False)

fig_combined.tight_layout()
fig_combined.savefig('outputs/gameplay_left_charts_combined.png', dpi=300, bbox_inches='tight')
print('Combined simplified left charts saved to outputs/gameplay_left_charts_combined.png')

plt.show()
