# data_processing.py - 数据处理模块（合并feature_detector）

# 标准库导入 
import os

# 第三方库导入 
import numpy as np
import pandas as pd
from tkinter import filedialog, messagebox

# 本地模块导入 
from config import OUTPUT_FILES, MZ_TOLERANCE
import data_store
from data_store import class_manager
from output_manager import output_manager
from utils import log_message
from validation_decorators import safe_data_processing





class FeatureDetector:
    """特征检测器 - 管理预测时的特征对齐和样本处理"""
    
    def __init__(self):
        self.training_features = None
        self.normalization_method = None  # 'max'/'sum'/'median'/None
        self.training_data_path = None
        self.log_transform = False
        self.scaling_method = None
        self.pareto_means = None
        self.pareto_stds = None
        self.half_min_values = {}
    
    def load_training_features(self, force_reload=False):
        """
        加载训练特征和归一化方法
        
        返回:
            tuple: (特征列表, 归一化方法) 或 (None, None)
        """
        if not force_reload and self.training_features is not None:
            return self.training_features, self.normalization_method
        
        try:
            # 获取训练数据路径
            data_file = data_store.get_training_data_path()
            if not data_file or not os.path.exists(data_file):
                data_file = OUTPUT_FILES['processed_data']
                if not os.path.exists(data_file):
                    log_message("训练数据文件不存在", "ERROR")
                    return None, None
            
            self.training_data_path = data_file
            log_message(f"使用训练数据: {data_file}", "INFO")
            
            # 读取特征名
            df = pd.read_csv(data_file, index_col=0)
            feature_names = df.index.tolist()[1:]  # 跳过'class'行
            
            # 解析为数值
            training_mz_values = []
            for name in feature_names:
                try:
                    training_mz_values.append(float(name))
                except ValueError:
                    log_message(f"无法解析特征名: {name}, 跳过", "WARNING")
            
            # 从文件名检测归一化方法
            self.normalization_method = self._detect_normalization_method()
            self.training_features = training_mz_values
            
            log_message(f"检测到 {len(training_mz_values)} 个特征", "SUCCESS")
            return training_mz_values, self.normalization_method
            
        except Exception as e:
            log_message(f"检测训练特征失败: {str(e)}", "ERROR")
            return None, None
    
    def _detect_normalization_method(self):
        """从文件名推断归一化方法"""
        if not self.training_data_path:
            return None
        
        basename = os.path.basename(self.training_data_path)
        
        if '_max' in basename:
            log_message("检测到归一化方法: max", "INFO")
            return 'max'
        elif '_sum' in basename:
            log_message("检测到归一化方法: sum", "INFO")
            return 'sum'
        elif '_median' in basename:
            log_message("检测到归一化方法: median", "INFO")
            return 'median'
        else:
            log_message("使用原始数据（无归一化）", "INFO")
            return None
        
    def process_prediction_sample(self, file_path, training_mz_values=None, norm_method=None):
        """
        处理预测样本文件
        
        参数:
            file_path: 样本文件路径
            training_mz_values: 训练特征列表（可选，自动加载）
            norm_method: 归一化方法（可选，自动检测）
            
        返回:
            np.array: 形状为 (1, n_features) 的特征向量
        """
        # 自动加载特征
        if training_mz_values is None:
            training_mz_values, detected_method = self.load_training_features()
            if training_mz_values is None:
                raise ValueError("无法检测训练特征")
            norm_method = norm_method if norm_method is not None else detected_method
        
        # 读取原始数据
        raw_data = pd.read_csv(file_path, sep=r'\s+', header=None)
        
        if raw_data.empty or raw_data.shape[1] < 2:
            raise ValueError(f"文件格式错误: {file_path}")
        
        # 计算归一化统计值
        intensities = raw_data.iloc[:, 1]
        sample_stats = {
            'max': intensities.max(),
            'sum': intensities.sum(),
            'median': intensities.median()
        } if norm_method else None
        
        # 提取特征
        results = []
        for target_mz in training_mz_values:
            intensity = self._extract_intensity(raw_data, target_mz, norm_method, sample_stats)
            # half-min 填补：用训练时记录的同特征 half_min 替换零值
            if intensity == 0.0 and self.half_min_values:
                half_min = self.half_min_values.get(str(target_mz))
                if half_min is not None:
                    intensity = half_min
            results.append(intensity)

        arr = np.array(results, dtype=float)

        # log₂(x+1) 变换
        if self.log_transform:
            arr = np.log2(arr + 1)

        # Pareto scaling
        if (self.scaling_method == 'pareto'
                and self.pareto_means is not None
                and self.pareto_stds is not None):
            means = np.array(self.pareto_means)
            stds = np.array(self.pareto_stds)
            stds = np.where(stds == 0, 1.0, stds)
            arr = (arr - means) / np.sqrt(stds)

        log_message(f"处理样本完成: {os.path.basename(file_path)}, 特征数: {len(arr)}")
        return arr.reshape(1, -1)
    
    def _extract_intensity(self, raw_data, target_mz, norm_method, sample_stats):
        """为指定m/z值提取强度"""
        lower = target_mz - MZ_TOLERANCE
        upper = target_mz + MZ_TOLERANCE
        
        filtered = raw_data[
            (raw_data.iloc[:, 0] >= lower) & 
            (raw_data.iloc[:, 0] <= upper)
        ]
        
        if filtered.empty:
            return 0.0
        
        max_intensity = filtered.iloc[:, 1].max()
        
        # 归一化
        if norm_method and sample_stats:
            factor = sample_stats.get(norm_method, 1)
            if factor > 0:
                return max_intensity / factor
        
        return max_intensity
        

@safe_data_processing(min_samples=5)
def open_data_file():
    """
    打开并加载已处理的特征矩阵.csv文件，准备机器学习模型训练。
        
    返回:
        tuple: (row, column, df, file_path) 特征矩阵、标签、DataFrame、文件路径
               失败时返回 (None, None, None, None)
    """
    initial_dir = str(output_manager.get_path('data', ''))
    if not os.path.exists(initial_dir):
        initial_dir = "/"
    
    file_path = filedialog.askopenfilename(
        initialdir=initial_dir,
        title="选择CSV文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        log_message("用户取消了文件选择")
        return None, None, None, None
    
    data_store.set_training_data_path(file_path)
    log_message(f"正在加载文件: {os.path.basename(file_path)}")
    
    df = pd.read_csv(file_path, index_col=0)

    data_store.clear_file_classification()
    log_message("数据文件已成功加载")

    # 解析数据
    row = df.iloc[1:, :].values.T
    ylabels = pd.Series(df.iloc[0, :].values).astype(str)

    # 保存类别信息到datastore
    unique_labels = ylabels.unique()
    if len(unique_labels) >= 2:
        data_store.set_file_classification({
            'class_0_name': str(unique_labels[0]),
            'class_1_name': str(unique_labels[1]),
            'class_0_files': [],
            'class_1_files': []
        })
        log_message(f"从CSV读取类别: {unique_labels[0]}, {unique_labels[1]}")
        
    log_message(f"数据形状: {row.shape}, 样本数: {row.shape[0]}, 特征数: {row.shape[1]}")
    log_message(f"类别标签统计: {dict(ylabels.value_counts())}")

    if len(ylabels.value_counts()) < 2:
        messagebox.showwarning("警告", "数据中只有一种类别，需要至少两种类别才能训练模型")
        
    # 标签编码
    column = np.array([class_manager.encode(label) for label in ylabels])
    log_message("标签编码完成，数据预处理成功")

    return row, column, df, file_path