import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import LabelEncoder 
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import KFold

def custom_score(estimator, X, y):
    # 获取预测值并二值化
    y_pred = estimator.predict(X)
    y_pred_binary = (y_pred > 0.5).astype(int)
    return balanced_accuracy_score(y, y_pred_binary)

def find_best_n_components(X, y, max_components=10):
    scores = []
    components_range = range(1, max_components + 1)
    
    for n in components_range:
        pls = PLSRegression(n_components=n)
        # 使用自定义评分函数
        score = cross_val_score(pls, X, y, cv=5, scoring=custom_score)
        scores.append(np.mean(score))
        print(f"组件数 {n}: 平均准确率 = {np.mean(score):.4f} (±{np.std(score):.4f})")
    
    best_n_components = components_range[np.argmax(scores)]
    
    plt.figure(figsize=(10, 6))
    plt.plot(components_range, scores, 'bo-')
    plt.axvline(best_n_components, color='r', linestyle='--')
    plt.xlabel('Number of Components')
    plt.ylabel('Balanced Accuracy')
    plt.title('Model Performance vs Number of Components')
    plt.grid(True)
    plt.show()
    
    return best_n_components, scores

# 读取数据
df = pd.read_excel('LC_MAX.xlsx')
df = df.iloc[:, 1:]  # 去掉第一列

# 转置数据以匹配样本和特征
X = df.iloc[1:, :].values.T  # 现在转置是正确的
y = df.iloc[0, :].values    # 标签向量

# 标签编码
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# 打印形状检查
print("X shape:", X.shape)
print("y shape:", y_encoded.shape)

# 找最佳组件数
best_n, scores = find_best_n_components(X, y_encoded, max_components=min(15, X.shape[1]))
print(f"\n最佳组件数量是: {best_n}")