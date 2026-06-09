import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

"""
Visualization: Bonus Optimization Heatmap
Reads results from optimization script (08) and creates heatmap visualization.
Shows standard deviation across Bronze vs Gold bonus parameter space.
No simulations are run here - just visualization of existing results.
"""

print("="*80)
print("BONUS OPTIMIZATION VISUALIZATION")
print("="*80)

# Load optimization results
with open('outputs/bonus_optimization_results.json', 'r') as f:
    data = json.load(f)

print(f"Loaded results from {len(data['configurations'])} configurations")
print(f"Each tested with {data['num_iterations']} Monte Carlo iterations")
print(f"Penalty mode: {data['penalty_mode']}\n")

# We'll create a simplified heatmap: Bronze vs Gold (fix Silver at 50)
# Extract unique values
bronze_values = sorted(list(set(c['bronze_bonus'] for c in data['configurations'])))
silver_values = sorted(list(set(c['silver_bonus'] for c in data['configurations'])))
gold_values = sorted(list(set(c['gold_bonus'] for c in data['configurations'])))

print(f"Bronze bonus values tested: {bronze_values}")
print(f"Silver bonus values tested: {silver_values}")
print(f"Gold bonus values tested: {gold_values}\n")

# For visualization, we'll create Bronze vs Gold heatmap for Silver=50
# (or use the middle silver value if 50 isn't available)
target_silver = 50 if 50 in silver_values else silver_values[len(silver_values)//2]
print(f"Creating heatmap for Bronze vs Gold (Silver fixed at {target_silver})\n")

# Filter configurations for target silver value
filtered_configs = [c for c in data['configurations'] if c['silver_bonus'] == target_silver]

if not filtered_configs:
    print("ERROR: No configurations found with Silver={target_silver}")
    exit(1)

# Build results matrix
results_matrix = np.zeros((len(gold_values), len(bronze_values)))
for config in filtered_configs:
    i = gold_values.index(config['gold_bonus'])
    j = bronze_values.index(config['bronze_bonus'])
    results_matrix[i, j] = config['std_dev']

# Find optimal configuration (among filtered configs)
min_idx = np.unravel_index(results_matrix.argmin(), results_matrix.shape)
optimal_bronze = bronze_values[min_idx[1]]
optimal_gold = gold_values[min_idx[0]]
optimal_std_dev = results_matrix[min_idx]

print(f"Optimal Configuration (Silver={target_silver}): Bronze={optimal_bronze}, Gold={optimal_gold}")
print(f"Standard Deviation: {optimal_std_dev:.1f} points\n")

print("Creating heatmap...")

# Create visualization
fig, ax = plt.subplots(figsize=(10, 8))

# Create heatmap (green=good, red=bad)
sns.heatmap(results_matrix, 
            annot=True, 
            fmt='.1f',
            xticklabels=bronze_values,
            yticklabels=gold_values,
            cmap='RdYlGn_r',
            cbar_kws={'label': 'Standard Deviation (points)'},
            ax=ax,
            vmin=0,
            linewidths=0.5,
            linecolor='gray')

ax.set_xlabel('Bronze Bonus', fontsize=13, fontweight='bold')
ax.set_ylabel('Gold Bonus', fontsize=13, fontweight='bold')
ax.set_title(f'Bonus Optimization Heatmap\n(Silver={target_silver}, Monte Carlo: 50 iterations per config)', 
             fontsize=14, fontweight='bold', pad=15)

# Mark optimal point
ax.plot(min_idx[1] + 0.5, min_idx[0] + 0.5, 
        marker='*', markersize=25, color='blue', 
        markeredgecolor='white', markeredgewidth=2,
        label=f'Optimal: Bronze={optimal_bronze}, Gold={optimal_gold}')

ax.legend(loc='upper right', fontsize=11)

plt.tight_layout()
plt.savefig('outputs/bonus_optimization_heatmap.png', dpi=300, bbox_inches='tight')
print("Heatmap saved to outputs/bonus_optimization_heatmap.png")
plt.show()
