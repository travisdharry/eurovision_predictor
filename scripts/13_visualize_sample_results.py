import os

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    input_path = 'data/SampleResults.csv'
    output_path = 'outputs/sample_results_player_scores.png'

    os.makedirs('outputs', exist_ok=True)

    df = pd.read_csv(input_path)

    required_columns = {'Player', 'Score'}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")

    plot_df = df[['Player', 'Score']].copy().sort_values('Score', ascending=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(plot_df['Player'], plot_df['Score'], color='#2E86AB', edgecolor='none', alpha=0.9)

    ax.set_title('Score by Player', fontsize=14, fontweight='bold')
    ax.set_xlabel('Fantasy Score', fontsize=11)
    ax.set_ylabel('')
    ax.invert_yaxis()  # Keep highest score at the top

    # Remove grid lines, borders, axes, and tick marks.
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis='x', which='both', length=0)
    ax.tick_params(axis='y', which='both', length=0)

    # Add value labels at the end of each horizontal bar.
    for bar in bars:
        width = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax.text(
            width,
            y,
            f' {int(width)}',
            ha='left',
            va='center',
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f'Visualization saved to: {output_path}')


if __name__ == '__main__':
    main()
