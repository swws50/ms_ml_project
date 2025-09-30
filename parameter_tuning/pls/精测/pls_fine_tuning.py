import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler

# ============================
# 第一步：精细参数搜索
# ============================
print("Starting fine-tuning parameter search...")

# Read data
df = pd.read_csv('raw_ms_data.csv')
X = df.iloc[1:, 1:].T
y = df.iloc[0, 1:]
X_scaled = StandardScaler().fit_transform(X)

# Fine-grained parameter search around the best parameters
param_grid = {
    'n_components': range(2, 8),           # Test 2-7 around 4
    'scale': [True, False],                
    'max_iter': [300, 500, 800, 1000],     # More iteration options
    'tol': [1e-6, 1e-5, 1e-4]              # Add convergence tolerance test
}

grid_search = GridSearchCV(
    PLSRegression(),
    param_grid,
    cv=KFold(5, shuffle=True, random_state=42),
    scoring='r2',
    n_jobs=-1,
    verbose=1,
    return_train_score=True  # Also return training scores
)

grid_search.fit(X_scaled, y)

print(f"\n✅ Fine-tuning completed!")
print(f"Best parameters: {grid_search.best_params_}")
print(f"Best R² score: {grid_search.best_score_:.4f}")

# Save results
results_df = pd.DataFrame(grid_search.cv_results_)
results_df.to_csv('pls_fine_tuned_results.csv', index=False)
print("Results saved to pls_fine_tuned_results.csv")

# ============================
# 第二步：生成可视化
# ============================
print("\nGenerating visualization figures...")

# Set style
sns.set_style("whitegrid")

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Figure 1: R² score vs n_components (grouped by scale and tol)
ax1 = fig.add_subplot(gs[0, :2])
for scale_val in [True, False]:
    for tol_val in results_df['param_tol'].unique():
        subset = results_df[(results_df['param_scale'] == scale_val) & 
                           (results_df['param_tol'] == tol_val)]
        scores = subset.groupby('param_n_components')['mean_test_score'].mean()
        label = f"scale={scale_val}, tol={tol_val}"
        ax1.plot(scores.index, scores.values, marker='o', label=label, linewidth=2)
ax1.set_xlabel('Number of Components', fontsize=12)
ax1.set_ylabel('Mean R² Score', fontsize=12)
ax1.set_title('Fine-tuning: R² Score vs Number of Components', fontsize=14, fontweight='bold')
ax1.legend(fontsize=8, ncol=2)
ax1.grid(True, alpha=0.3)

# Figure 2: Top 15 best combinations
ax2 = fig.add_subplot(gs[0, 2])
top15 = results_df.nsmallest(15, 'rank_test_score')
labels = [f"n={int(r['param_n_components'])}\ntol={r['param_tol']}" 
          for _, r in top15.iterrows()]
colors = plt.cm.RdYlGn(top15['mean_test_score'] / top15['mean_test_score'].max())
ax2.barh(range(15), top15['mean_test_score'].values, color=colors)
ax2.set_yticks(range(15))
ax2.set_yticklabels(labels, fontsize=7)
ax2.set_xlabel('R²', fontsize=10)
ax2.set_title('Top 15', fontsize=12, fontweight='bold')
ax2.invert_yaxis()

# Figure 3: Heatmap - n_components vs tol (scale=False)
ax3 = fig.add_subplot(gs[1, 0])
pivot_false = results_df[results_df['param_scale'] == False].pivot_table(
    values='mean_test_score', 
    index='param_tol', 
    columns='param_n_components',
    aggfunc='mean'
)
sns.heatmap(pivot_false, annot=True, fmt='.4f', cmap='RdYlGn', ax=ax3, cbar_kws={'label': 'R²'})
ax3.set_title('Heatmap (scale=False)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Number of Components', fontsize=10)
ax3.set_ylabel('Tolerance (tol)', fontsize=10)

# Figure 4: Heatmap - n_components vs tol (scale=True)
ax4 = fig.add_subplot(gs[1, 1])
pivot_true = results_df[results_df['param_scale'] == True].pivot_table(
    values='mean_test_score', 
    index='param_tol', 
    columns='param_n_components',
    aggfunc='mean'
)
sns.heatmap(pivot_true, annot=True, fmt='.4f', cmap='RdYlGn', ax=ax4, cbar_kws={'label': 'R²'})
ax4.set_title('Heatmap (scale=True)', fontsize=12, fontweight='bold')
ax4.set_xlabel('Number of Components', fontsize=10)
ax4.set_ylabel('Tolerance (tol)', fontsize=10)

# Figure 5: max_iter impact
ax5 = fig.add_subplot(gs[1, 2])
iter_comparison = results_df.groupby('param_max_iter')['mean_test_score'].agg(['mean', 'max'])
ax5.bar(iter_comparison.index.astype(str), iter_comparison['mean'], alpha=0.7, label='Mean')
ax5.plot(range(len(iter_comparison)), iter_comparison['max'], 'ro-', linewidth=2, label='Max')
ax5.set_xlabel('max_iter', fontsize=10)
ax5.set_ylabel('R² Score', fontsize=10)
ax5.set_title('Impact of max_iter', fontsize=12, fontweight='bold')
ax5.legend()
ax5.grid(True, alpha=0.3, axis='y')

# Figure 6: Train vs Test score comparison (check overfitting)
ax6 = fig.add_subplot(gs[2, :])
top20 = results_df.nsmallest(20, 'rank_test_score')
x = range(len(top20))
ax6.plot(x, top20['mean_train_score'].values, 'b-o', label='Train Score', linewidth=2)
ax6.plot(x, top20['mean_test_score'].values, 'r-s', label='Test Score', linewidth=2)
ax6.fill_between(x, 
                  top20['mean_test_score'] - top20['std_test_score'],
                  top20['mean_test_score'] + top20['std_test_score'],
                  alpha=0.2, color='red')
ax6.set_xlabel('Parameter Combination Rank', fontsize=12)
ax6.set_ylabel('R² Score', fontsize=12)
ax6.set_title('Train vs Test Score (Top 20)', fontsize=14, fontweight='bold')
ax6.legend()
ax6.grid(True, alpha=0.3)
ax6.set_xticks(x)
ax6.set_xticklabels([f"{int(r['param_n_components'])}" for _, r in top20.iterrows()], rotation=0)

plt.savefig('pls_fine_tuned_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Figure saved as pls_fine_tuned_analysis.png")

# ============================
# 第三步：输出详细报告
# ============================
print("\n" + "="*60)
print("PLS 精细调优结果报告")
print("="*60)

best = results_df.loc[results_df['rank_test_score'] == 1].iloc[0]
print(f"\n🏆 Best Parameter Combination:")
print(f"   - n_components: {int(best['param_n_components'])}")
print(f"   - scale: {best['param_scale']}")
print(f"   - max_iter: {int(best['param_max_iter'])}")
print(f"   - tol: {best['param_tol']}")
print(f"   - Test R²: {best['mean_test_score']:.4f} (±{best['std_test_score']:.4f})")
print(f"   - Train R²: {best['mean_train_score']:.4f}")
print(f"   - Overfitting degree: {(best['mean_train_score'] - best['mean_test_score']):.4f}")

print(f"\n📊 Top 10 Parameter Combinations:")
for i, (_, row) in enumerate(results_df.nsmallest(10, 'rank_test_score').iterrows(), 1):
    print(f"   {i}. n={int(row['param_n_components'])}, scale={row['param_scale']}, "
          f"iter={int(row['param_max_iter'])}, tol={row['param_tol']} "
          f"→ R²={row['mean_test_score']:.4f}")

print(f"\n💡 Parameter Impact Analysis:")
print(f"   - Optimal n_components: {int(results_df.loc[results_df['mean_test_score'].idxmax(), 'param_n_components'])}")
scale_diff = abs(results_df.groupby('param_scale')['mean_test_score'].mean().diff().iloc[-1])
tol_std = results_df.groupby('param_tol')['mean_test_score'].mean().std()
iter_std = results_df.groupby('param_max_iter')['mean_test_score'].mean().std()
print(f"   - scale impact: {'Significant' if scale_diff > 0.01 else 'Insignificant'} (diff: {scale_diff:.4f})")
print(f"   - tol impact: {'Significant' if tol_std > 0.01 else 'Insignificant'} (std: {tol_std:.4f})")
print(f"   - max_iter impact: {'Significant' if iter_std > 0.01 else 'Insignificant'} (std: {iter_std:.4f})")

print("\n" + "="*60)
print("✅ Fine-tuning completed!")
print("="*60)