# feature_detector.py - 特征检测和处理模块

# 标准库导入 
import os

# 第三方库导入 
import numpy as np
import pandas as pd

# 本地模块导入 
from config import OUTPUT_FILES, MZ_TOLERANCE, get_normalization_factor
import data_store
from utils import log_message


class FeatureDetector:
    """特征检测器类 - 统一管理特征检测和样本处理"""
    
    def __init__(self):
        self.training_features = None
        self.normalization_factor = None
        self.training_data_path = None
    
    def load_training_features(self, force_reload=False):
        """
        检测训练特征和归一化因子
        
        参数:
            force_reload: 是否强制重新检测
            
        返回:
            tuple: (特征列表, 归一化因子) 或 (None, None)
        """
        # 如果已经检测过且不需要强制重新加载
        if not force_reload and self.training_features is not None:
            return self.training_features, self.normalization_factor
        
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
            
            # 读取和解析特征
            df = pd.read_csv(data_file, index_col=0)
            feature_names = df.index.tolist()[1:]  # 跳过'class'行
            
            # 检测归一化因子
            normalization_factor = self._detect_normalization_factor(df)
            
            # 转换特征名为数值
            training_mz_values = []
            for feature_name in feature_names:
                try:
                    mz_value = float(feature_name)
                    training_mz_values.append(mz_value)
                except ValueError:
                    log_message(f"无法解析特征名: {feature_name}，跳过", "WARNING")
            
            # 缓存结果
            self.training_features = training_mz_values
            self.normalization_factor = normalization_factor
            self.training_data_path = data_file
            
            log_message(f"检测到 {len(training_mz_values)} 个特征", "SUCCESS")
            return training_mz_values, normalization_factor
            
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
        """
        检测归一化因子
        
        参数:
            df: 训练数据DataFrame
            
        返回:
            float: 归一化因子
        """
        # 优先使用配置管理中的统一函数
        factor = get_normalization_factor()
        
        # 如果是默认值，尝试从训练数据推断
        try:
            max_training_value = df.iloc[1:, :].max().max()  # 跳过class行
            
            if 0.8 <= max_training_value <= 1.2:
                log_message("训练数据已归一化，使用配置文件的因子", "INFO")
            else:
                log_message("使用训练数据最大值作为归一化因子", "INFO")
                factor = max_training_value
                
        except Exception as e:
            log_message(f"推断归一化因子失败: {str(e)}，使用默认值", "WARNING")
        
        log_message(f"最终使用归一化因子: {factor:.2f}", "INFO")
        return factor
    
    def process_prediction_sample(self, file_path, training_mz_values=None, normalization_factor=None):
        """
        处理预测样本文件
        
        参数:
            file_path: 样本文件路径
            training_mz_values: 训练特征列表（可选，如果未提供则自动检测）
            normalization_factor: 归一化因子（可选，如果未提供则自动检测）
            
        返回:
            numpy.ndarray: 处理后的特征矩阵
        """
        # 如果未提供特征信息，自动检测
        if training_mz_values is None or normalization_factor is None:
            detected_features, detected_factor = self.load_training_features()
            if detected_features is None:
                raise ValueError("无法检测训练特征")
            
            training_mz_values = training_mz_values or detected_features
            normalization_factor = normalization_factor or detected_factor
        
        try:
            # 读取原始数据
            raw_data = pd.read_csv(file_path, sep=r'\s+', header=None)
            
            if raw_data.empty or raw_data.shape[1] < 2:
                raise ValueError(f"文件格式错误: {file_path}")
            
            results = []
            
            # 对每个训练特征提取强度
            for target_mz in training_mz_values:
                intensity = self._extract_intensity_for_mz(raw_data, target_mz, normalization_factor)
                results.append(intensity)
            
            log_message(f"处理样本完成: {os.path.basename(file_path)}, 特征数: {len(results)}")
            return np.array(results).reshape(1, -1)
            
        except Exception as e:
            log_message(f"处理预测样本失败: {str(e)}", "ERROR")
            raise
    
    def _extract_intensity_for_mz(self, raw_data, target_mz, normalization_factor):
        """
        为指定m/z值提取强度
        
        参数:
            raw_data: 原始数据DataFrame
            target_mz: 目标m/z值
            normalization_factor: 归一化因子
            
        返回:
            float: 归一化后的强度值
        """
        lower_bound = target_mz - MZ_TOLERANCE
        upper_bound = target_mz + MZ_TOLERANCE
        
        # 在容差范围内查找
        filtered_df = raw_data[
            (raw_data.iloc[:, 0] >= lower_bound) & 
            (raw_data.iloc[:, 0] <= upper_bound)
        ]
        
        if not filtered_df.empty:
            max_intensity = filtered_df.iloc[:, 1].max()
            normalized_intensity = max_intensity / normalization_factor
        else:
            normalized_intensity = 0.0
        
        return normalized_intensity
    
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



