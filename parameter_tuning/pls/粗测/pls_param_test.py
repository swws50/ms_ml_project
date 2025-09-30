import pandas as pd
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler

# 读取数据（转置格式）
df = pd.read_csv("C:/Users/wj611/Desktop/参数测试/raw_ms_data.csv")
X = df.iloc[1:, 1:].T  # 转置：每行是样本，每列是m/z特征
y = df.iloc[0, 1:]     # 第0行从第1列开始是class标签

# 数据标准化
X_scaled = StandardScaler().fit_transform(X)

# 定义参数网格
param_grid = {
    'n_components': range(1, min(20, X.shape[1]) + 1),  # 测试1-20个成分
    'scale': [True, False],                              # 是否缩放
    'max_iter': [500, 1000],                             # 最大迭代次数
}

# 网格搜索
grid_search = GridSearchCV(
    PLSRegression(),
    param_grid,
    cv=KFold(5, shuffle=True, random_state=42),
    scoring='r2',
    n_jobs=-1,
    verbose=2
)

# 训练
grid_search.fit(X_scaled, y)

# 输出结果
print(f"\n最佳参数: {grid_search.best_params_}")
print(f"最佳R²得分: {grid_search.best_score_:.4f}")

# 保存所有结果
results_df = pd.DataFrame(grid_search.cv_results_)
results_df.to_csv('pls_grid_search_results.csv', index=False)
print("\n结果已保存到 pls_grid_search_results.csv")