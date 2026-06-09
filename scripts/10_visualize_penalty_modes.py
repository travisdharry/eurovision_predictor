import json
import numpy as np
import matplotlib.pyplot as plt

"""
Visualization: Penalty Mode Comparison
Reads results from penalty mode optimization and creates comparison visualization.
Shows how different penalty modes affect gameplay balance.
"""

print("="*80)
print("PENALTY MODE COMPARISON VISUALIZATION")
print("="*80)

# Load optimization results
with open('outputs/penalty_mode_optimization_results.json', 'r') as f:
    data = json.load(f)

print(f"Loaded results from {len(data['configurations'])} configurations")
print(f"Each tested with {data['num_iterations']} Monte Carlo iterations\n")

# Build lookup by penalty mode (one config per mode in isolated test)
mode_to_config = {c['mode']: c for c in data['configurations']}
ordered_modes = ['none', 'winner_only', 'full']
ordered_mode_labels = ['A: No Penalties', 'B: Winner Only', 'C: Full Penalties']
ordered_configs = [mode_to_config[m] for m in ordered_modes]

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle(f"Penalty Mode A/B/C Comparison (Isolated Mode Change)\n(Monte Carlo: {data['num_iterations']} iterations per mode)", 
             fontsize=16, fontweight='bold', y=0.995)

# Panel 1: Standard Deviation Comparison
ax1 = axes[0, 0]
labels = ordered_mode_labels
std_devs = [c['std_dev'] for c in ordered_configs]
colors = ['#2ecc71', '#3498db', '#e74c3c']

y_pos = np.arange(len(labels))
bars = ax1.barh(y_pos, std_devs, color=colors, alpha=0.7, edgecolor='black', linewidth=1)

# Highlight best configuration
best_idx = std_devs.index(min(std_devs))
bars[best_idx].set_alpha(1.0)
bars[best_idx].set_edgecolor('gold')
bars[best_idx].set_linewidth(3)

ax1.set_yticks(y_pos)
ax1.set_yticklabels(labels, fontsize=9)
ax1.set_xlabel('Standard Deviation (points)', fontsize=11, fontweight='bold')
ax1.set_title('Balance Score by Penalty Mode', fontsize=12, fontweight='bold')
ax1.invert_yaxis()
ax1.grid(axis='x', alpha=0.3, linestyle='--')

# Add legend for modes
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#2ecc71', alpha=0.7, label='No Penalties'),
    Patch(facecolor='#3498db', alpha=0.7, label='Winner Only'),
    Patch(facecolor='#e74c3c', alpha=0.7, label='Full Penalties')
]
ax1.legend(handles=legend_elements, loc='lower right', fontsize=9)

# Panel 2: Score Range Comparison
ax2 = axes[0, 1]
score_ranges = [c['range'] for c in ordered_configs]
ax2.bar(labels, score_ranges, color=colors, alpha=0.75, edgecolor='black', linewidth=1)
ax2.set_ylabel('Score Range (points)', fontsize=11, fontweight='bold')
ax2.set_title('Range by Penalty Mode', fontsize=12, fontweight='bold')
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.tick_params(axis='x', rotation=15)

# Panel 3: Position Score Distribution by Mode
ax3 = axes[1, 0]
best_none = mode_to_config['none']
best_winner = mode_to_config['winner_only']
best_full = mode_to_config['full']

positions = np.arange(1, 9)
width = 0.25

ax3.bar(positions - width, best_none['position_means'], width, 
        label='No Penalties', color='#2ecc71', alpha=0.7, edgecolor='black')
ax3.bar(positions, best_winner['position_means'], width,
        label='Winner Only', color='#3498db', alpha=0.7, edgecolor='black')
ax3.bar(positions + width, best_full['position_means'], width,
        label='Full Penalties', color='#e74c3c', alpha=0.7, edgecolor='black')

ax3.set_xlabel('Draft Position', fontsize=11, fontweight='bold')
ax3.set_ylabel('Average Score (points)', fontsize=11, fontweight='bold')
ax3.set_title('Position Means by Penalty Mode', fontsize=12, fontweight='bold')
ax3.set_xticks(positions)
ax3.legend(fontsize=9)
ax3.grid(axis='y', alpha=0.3, linestyle='--')

# Panel 4: Summary Table (Isolated Test)
ax4 = axes[1, 1]
ax4.axis('off')

summary_data = []
for mode_label, config in zip(ordered_mode_labels, ordered_configs):
    summary_data.append([
        mode_label,
        mode_label[0],
        f"{config['std_dev']:.1f}",
        f"{config['range']:.1f}",
        config['mode']
    ])

table = ax4.table(cellText=summary_data,
                  colLabels=['Penalty Mode', 'Arm', 'Std Dev', 'Range', 'Mode'],
                  cellLoc='left',
                  loc='center',
                  colWidths=[0.34, 0.1, 0.16, 0.16, 0.18])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.5)

# Style header
for i in range(5):
    table[(0, i)].set_facecolor('#34495e')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Color rows by mode
colors = ['#2ecc71', '#3498db', '#e74c3c']
for i, color in enumerate(colors, 1):
    for j in range(5):
        table[(i, j)].set_facecolor(color)
        table[(i, j)].set_alpha(0.3)

# Highlight best overall
overall_best = min(ordered_configs, key=lambda x: x['std_dev'])
best_row = ordered_configs.index(overall_best) + 1
for j in range(5):
    table[(best_row, j)].set_edgecolor('gold')
    table[(best_row, j)].set_linewidth(3)

ax4.set_title('Summary (Fixed Token Values Across Arms)', fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('outputs/penalty_mode_comparison.png', dpi=300, bbox_inches='tight')
print("Visualization saved to outputs/penalty_mode_comparison.png")
plt.show()
