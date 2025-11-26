# feature_detector.py - 特征检测和处理模块

# 标准库导入 
import os

# 第三方库导入 
import numpy as np
import pandas as pd

# 本地模块导入 
from config import OUTPUT_FILES, MZ_TOLERANCE
import data_store
from utils import log_message


class FeatureDetector:
    """特征检测器类 - 统一管理特征检测和样本处理"""
    
    def __init__(self):
        self.training_features = None
        self.normalization_method = None  # 改名：'max'/'sum'/'median'/None
        self.training_data_path = None
    
    def load_training_features(self, force_reload=False):
        """
        检测训练特征和归一化方法
        
        返回:
            tuple: (特征列表, 归一化方法) 或 (None, None)
                归一化方法为 'max'/'sum'/'median'/None
        """
        need_reload = (
            force_reload or 
            self.training_features is None
        )
        
        if not need_reload:
            return self.training_features, self.normalization_method
        
        try:
            # 方法1: 优先从data_store获取训练数据路径
            stored_path = self._get_stored_training_path()
            if stored_path and os.path.exists(stored_path):
                data_file = stored_path
                log_message(f"使用存储的训练数据路径: {data_file}", "INFO")
            else:
                # 方法2: 使用默认路径
                data_file = OUTPUT_FILES['processed_data']
                if not os.path.exists(data_file):
                    log_message("训练数据文件不存在", "ERROR")
                    return None, None
                log_message(f"使用默认训练数据路径: {data_file}", "INFO")
            
            self.training_data_path = data_file
            
            # 读取和解析特征
            df = pd.read_csv(data_file, index_col=0)
            feature_names = df.index.tolist()[1:]  # 跳过'class'行
            
            # 从文件名检测归一化方法
            norm_method, _ = self._detect_normalization_factor(df)
            
            # 转换特征名为数值
            training_mz_values = []
            for feature_name in feature_names:
                try:
                    mz_value = float(feature_name)
                    training_mz_values.append(mz_value)
                except ValueError:
                    log_message(f"无法解析特征名: {feature_name},跳过", "WARNING")
            
            # 缓存结果
            self.training_features = training_mz_values
            self.normalization_method = norm_method  # 改为存储方法名
            
            log_message(f"检测到 {len(training_mz_values)} 个特征", "SUCCESS")
            return training_mz_values, norm_method
            
        except Exception as e:
            log_message(f"检测训练特征失败: {str(e)}", "ERROR")
            return None, None
        
    def _get_stored_training_path(self):
        """获取存储的训练数据路径"""
        try:
            stored_path = data_store.get_training_data_path()
            if stored_path:
                log_message(f"从data_store获取训练数据路径: {stored_path}", "INFO")
                return stored_path
        except Exception as e:
            log_message(f"获取存储路径失败: {str(e)}", "WARNING")
        
        return None
    
    def _detect_normalization_factor(self, df):
        """从训练数据文件名推断归一化方法"""
        if not self.training_data_path:
            log_message("无法确定归一化方法，使用原始数据", "WARNING")
            return None, None
        
        basename = os.path.basename(self.training_data_path)
        
        if '_max' in basename:
            log_message("检测到归一化方法: max（最大峰）", "INFO")
            return 'max', None
        elif '_sum' in basename:
            log_message("检测到归一化方法: sum（TIC）", "INFO")
            return 'sum', None
        elif '_median' in basename:
            log_message("检测到归一化方法: median（中位数）", "INFO")
            return 'median', None
        elif '_raw' in basename:
            log_message("检测到数据模式: raw（未归一化）", "INFO")
            return None, None
        else:
            log_message("无法从文件名推断归一化方法，使用原始数据", "WARNING")
            return None, None
        
    def process_prediction_sample(self, file_path, training_mz_values=None, norm_method=None):
        """
        处理预测样本文件
        
        参数:
            file_path: 样本文件路径
            training_mz_values: 训练特征列表
            norm_method: 归一化方法 ('max'/'sum'/'median'/None)
        """
        if training_mz_values is None or norm_method is None:
            detected_features, detected_method = self.load_training_features()
            if detected_features is None:
                raise ValueError("无法检测训练特征")
            
            training_mz_values = training_mz_values or detected_features
            norm_method = norm_method if norm_method is not None else detected_method
        
        try:
            # 读取原始数据
            raw_data = pd.read_csv(file_path, sep=r'\s+', header=None)
            
            if raw_data.empty or raw_data.shape[1] < 2:
                raise ValueError(f"文件格式错误: {file_path}")
            
            # 计算样本统计值（用于归一化）
            intensities = raw_data.iloc[:, 1]
            sample_stats = {
                'max': intensities.max(),
                'sum': intensities.sum(),
                'median': intensities.median()
            } if norm_method else None
            
            results = []
            
            # 对每个训练特征提取强度
            for target_mz in training_mz_values:
                intensity = self._extract_intensity_for_mz(raw_data, target_mz, norm_method, sample_stats)
                results.append(intensity)
            
            log_message(f"处理样本完成: {os.path.basename(file_path)}, 特征数: {len(results)}")
            return np.array(results).reshape(1, -1)
            
        except Exception as e:
            log_message(f"处理预测样本失败: {str(e)}", "ERROR")
            raise
        
    def _extract_intensity_for_mz(self, raw_data, target_mz, norm_method, sample_stats):
        """
        为指定m/z值提取强度
        
        参数:
            raw_data: 原始数据DataFrame
            target_mz: 目标m/z值
            norm_method: 归一化方法 ('max'/'sum'/'median'/None)
            sample_stats: 样本统计值字典 {'max': x, 'sum': y, 'median': z}
        """
        lower_bound = target_mz - MZ_TOLERANCE
        upper_bound = target_mz + MZ_TOLERANCE
        
        filtered_df = raw_data[
            (raw_data.iloc[:, 0] >= lower_bound) & 
            (raw_data.iloc[:, 0] <= upper_bound)
        ]
        
        if not filtered_df.empty:
            max_intensity = filtered_df.iloc[:, 1].max()
            
            # 根据归一化方法处理
            if norm_method and sample_stats:
                norm_factor = sample_stats.get(norm_method)
                if norm_factor and norm_factor > 0:
                    return max_intensity / norm_factor
            
            return max_intensity
        else:
            return 0.0
        
    def validate_sample_file(self, file_path):
        """
        验证样本文件格式
        
        参数:
            file_path: 文件路径
            
        返回:
            tuple: (是否有效, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.txt'):
                return False, "文件格式不正确，需要.txt格式"
            
            # 检查文件内容
            data = pd.read_csv(file_path, sep=r'\s+', header=None, nrows=5)
            
            if data.empty:
                return False, "文件为空"
            
            if data.shape[1] < 2:
                return False, "文件格式错误，需要至少两列数据（m/z和强度）"
            
            # 检查数据类型
            try:
                data.iloc[:, 0].astype(float)  # m/z列
                data.iloc[:, 1].astype(float)  # 强度列
            except ValueError:
                return False, "数据格式错误，m/z和强度必须是数值"
            
            return True, "文件格式正确"
            
        except Exception as e:
            return False, f"文件验证失败: {str(e)}"
    
    def get_feature_info(self):
        """
        获取当前特征信息
        
        返回:
            dict: 特征信息字典
        """
        if self.training_features is None:
            self.load_training_features()
        
        return {
            "n_features": len(self.training_features) if self.training_features else 0,
            "mz_range": (
                min(self.training_features), 
                max(self.training_features)
            ) if self.training_features else None,
            "normalization_factor": self.normalization_factor,
            "training_data_path": self.training_data_path,
            "tolerance": MZ_TOLERANCE
        }
    
    def clear_cache(self):
        """清空缓存的特征信息"""
        self.training_features = None
        self.normalization_factor = None
        self.training_data_path = None
        log_message("特征检测缓存已清空", "INFO")



