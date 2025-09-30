import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")

# Read results
df = pd.read_csv(r"C:\Users\wj611\Desktop\大创\版本迭代\parameter_tuning\pls\粗测\pls_grid_search_results.csv")

# Create figures
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Figure 1: R² score vs Number of components
scores_by_comp = df.groupby('param_n_components')['mean_test_score'].agg(['mean', 'max', 'std'])
axes[0, 0].plot(scores_by_comp.index, scores_by_comp['mean'], marker='o', linewidth=2, markersize=8, label='Mean R²')
axes[0, 0].plot(scores_by_comp.index, scores_by_comp['max'], marker='s', linewidth=2, markersize=6, linestyle='--', label='Max R²')
axes[0, 0].fill_between(scores_by_comp.index, 
                         scores_by_comp['mean'] - scores_by_comp['std'],
                         scores_by_comp['mean'] + scores_by_comp['std'],
                         alpha=0.2)
axes[0, 0].set_xlabel('Number of Components', fontsize=12)
axes[0, 0].set_ylabel('R² Score', fontsize=12)
axes[0, 0].set_title('R² Score vs Number of Components', fontsize=14, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Figure 2: Top 10 parameter combinations
top10 = df.nsmallest(10, 'rank_test_score')
labels = [f"n={int(row['param_n_components'])}, scale={row['param_scale']}" 
          for _, row in top10.iterrows()]
colors = plt.cm.RdYlGn(top10['mean_test_score'] / top10['mean_test_score'].max())
axes[0, 1].barh(range(10), top10['mean_test_score'].values, color=colors)
axes[0, 1].set_yticks(range(10))
axes[0, 1].set_yticklabels(labels, fontsize=9)
axes[0, 1].set_xlabel('R² Score', fontsize=12)
axes[0, 1].set_title('Top 10 Parameter Combinations', fontsize=14, fontweight='bold')
axes[0, 1].invert_yaxis()

# Figure 3: Scale parameter impact comparison
scale_comparison = df.groupby(['param_n_components', 'param_scale'])['mean_test_score'].mean().unstack()
scale_comparison.plot(kind='bar', ax=axes[1, 0], width=0.8)
axes[1, 0].set_xlabel('Number of Components', fontsize=12)
axes[1, 0].set_ylabel('Mean R² Score', fontsize=12)
axes[1, 0].set_title('Scale Parameter Impact Comparison', fontsize=14, fontweight='bold')
axes[1, 0].legend(['Scale=False', 'Scale=True'])
axes[1, 0].tick_params(axis='x', rotation=0)
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Figure 4: All parameter combinations scatter plot
scatter_data = df.copy()
scatter_data['color'] = scatter_data['param_scale'].map({True: 'orange', False: 'blue'})
for scale_val, color, label in [(True, 'orange', 'Scale=True'), (False, 'blue', 'Scale=False')]:
    subset = scatter_data[scatter_data['param_scale'] == scale_val]
    axes[1, 1].scatter(subset['param_n_components'], subset['mean_test_score'], 
                       c=color, s=80, alpha=0.6, label=label)
axes[1, 1].set_xlabel('Number of Components', fontsize=12)
axes[1, 1].set_ylabel('R² Score', fontsize=12)
axes[1, 1].set_title('All Parameter Combinations Distribution', fontsize=14, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pls_results_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Figure saved as pls_results_analysis.png")

# Output statistical summary
print("\n" + "="*50)
print("PLS Parameter Search Results Summary")
print("="*50)
best = df.loc[df['rank_test_score'] == 1].iloc[0]
print(f"\n🏆 Best Parameters:")
print(f"   - n_components: {int(best['param_n_components'])}")
print(f"   - scale: {best['param_scale']}")
print(f"   - max_iter: {int(best['param_max_iter'])}")
print(f"   - R² Score: {best['mean_test_score']:.4f} (±{best['std_test_score']:.4f})")

print(f"\n📊 Top 5 Parameter Combinations:")
for i, (_, row) in enumerate(df.nsmallest(5, 'rank_test_score').iterrows(), 1):
    print(f"   {i}. n={int(row['param_n_components'])}, scale={row['param_scale']}, "
          f"iter={int(row['param_max_iter'])} → R²={row['mean_test_score']:.4f}")
print("\n" + "="*50)