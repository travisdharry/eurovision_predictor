import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

"""
Visualization: Tier Size Optimization Heatmap
Reads results from optimization script (05) and creates heatmap visualization.
No simulations are run here - just visualization of existing results.
"""

print("="*80)
print("TIER SIZE OPTIMIZATION VISUALIZATION")
print("="*80)

# Load optimization results
with open('outputs/tier_size_optimization_results.json', 'r') as f:
    data = json.load(f)

print(f"Loaded results from {len(data['configurations'])} configurations")
print(f"Each tested with {data['num_iterations']} Monte Carlo iterations\n")

# Extract tier sizes and std devs
tier1_sizes = sorted(list(set(c['tier1_size'] for c in data['configurations'])))
tier2_sizes = sorted(list(set(c['tier2_size'] for c in data['configurations'])))

# Build results matrix
results_matrix = np.zeros((len(tier2_sizes), len(tier1_sizes)))
for config in data['configurations']:
    i = tier2_sizes.index(config['tier2_size'])
    j = tier1_sizes.index(config['tier1_size'])
    results_matrix[i, j] = config['std_dev']

# Find optimal configuration
min_idx = np.unravel_index(results_matrix.argmin(), results_matrix.shape)
optimal_tier1 = tier1_sizes[min_idx[1]]
optimal_tier2 = tier2_sizes[min_idx[0]]
optimal_std_dev = results_matrix[min_idx]

print(f"Optimal Configuration: T1={optimal_tier1}, T2={optimal_tier2}")
print(f"Standard Deviation: {optimal_std_dev:.1f} points\n")

print("Creating heatmap...")

# Create visualization
fig, ax = plt.subplots(figsize=(10, 8))

# Reverse the matrix rows so larger T2 values appear at top
results_matrix_reversed = results_matrix[::-1]

# Create heatmap with reversed colormap (green=good, red=bad)
sns.heatmap(results_matrix_reversed, 
            annot=True, 
            fmt='.1f',
            xticklabels=tier1_sizes,
            yticklabels=tier2_sizes[::-1],  # Reverse y-axis labels
            cmap='RdYlGn_r',
            cbar_kws={'label': 'Standard Deviation (points)'},
            ax=ax,
            vmin=0,
            linewidths=0.5,
            linecolor='gray')

ax.set_xlabel('Tier 1 Size', fontsize=13, fontweight='bold')
ax.set_ylabel('Tier 2 Size', fontsize=13, fontweight='bold')
ax.set_title(f"Tier Size Optimization Heatmap\n(Monte Carlo: {data['num_iterations']} iterations per config)", 
             fontsize=14, fontweight='bold', pad=15)

plt.tight_layout()
plt.savefig('outputs/tier_size_optimization_heatmap.png', dpi=300, bbox_inches='tight')
print("Heatmap saved to outputs/tier_size_optimization_heatmap.png")
plt.show()
