# model_predictor.py - 专门负责样本预测的模块

# ========== 标准库导入 ==========
import os

# ========== 第三方库导入 ==========
import customtkinter as ctk
import numpy as np
import pandas as pd
from joblib import load
from sklearn.cross_decomposition import PLSRegression
from tkinter import filedialog, messagebox

# ========== 本地模块导入 ==========
from config import OUTPUT_FILES, MZ_TOLERANCE, get_class_mapping
import data_store
from feature_detector import FeatureDetector
from utils import log_message
from validation_decorators import require_data_store, safe_model_operation


class ModelPredictor:
    """样本预测器类 - 统一管理所有预测相关功能"""
    
    def __init__(self):
        self.model = None
        self.feature_detector = FeatureDetector()
        self.class_mapping = {}
        self.reverse_class_mapping = {}
        self._update_class_mapping()
    
    def _update_class_mapping(self):
        """更新类别映射"""
        self.class_mapping, self.reverse_class_mapping = get_class_mapping()
    
    def load_model(self):
        """
        加载最佳模型
        
        返回:
            bool: 是否成功加载模型
        """
        try:
            # 优先从data_store获取
            self.model = data_store.get_best_model()
            
            if self.model is None:
                # 从文件加载
                model_path = OUTPUT_FILES['best_model']
                if not os.path.exists(model_path):
                    log_message(f"模型文件不存在: {model_path}", "ERROR")
                    return False
                
                self.model = load(model_path)
                log_message(f"从文件加载模型: {model_path}", "INFO")
            else:
                log_message("从数据存储模块获取模型", "INFO")
            
            return True
            
        except Exception as e:
            log_message(f"加载模型失败: {str(e)}", "ERROR")
            self.model = None
            return False
    
    def get_prediction_probability(self, features):
        """
        获取预测概率 - 统一的概率计算接口
        
        参数:
            features: 样本特征矩阵
            
        返回:
            tuple: (预测类别, 概率数组) 或 (None, None) 如果失败
        """
        if self.model is None:
            log_message("模型未加载", "ERROR")
            return None, None
        
        try:
            if isinstance(self.model, PLSRegression):
                return self._handle_pls_prediction(features)
            elif hasattr(self.model, 'predict_proba'):
                return self._handle_proba_prediction(features)
            elif hasattr(self.model, 'decision_function'):
                return self._handle_decision_prediction(features)
            else:
                return self._handle_basic_prediction(features)
                
        except Exception as e:
            log_message(f"预测过程中出错: {str(e)}", "ERROR")
            return None, None
    
    def _handle_pls_prediction(self, features):
        """处理PLS回归模型的预测"""
        raw_value = self.model.predict(features).flatten()[0]
        
        # 获取最优阈值
        try:
            threshold = np.mean(np.loadtxt(OUTPUT_FILES['pls_thresholds'], delimiter=","))
        except:
            threshold = 0.5
            log_message("未找到PLS阈值文件，使用默认阈值0.5", "WARNING")
        
        # 转换为概率
        prob1 = 1 / (1 + np.exp(-(raw_value - threshold) * 10))
        probs = np.array([1 - prob1, prob1])
        pred = 1 if raw_value > threshold else 0
        
        return pred, probs
    
    def _handle_proba_prediction(self, features):
        """处理有predict_proba方法的模型"""
        probs = self.model.predict_proba(features)[0]
        pred = self.model.predict(features)[0]
        return pred, probs
    
    def _handle_decision_prediction(self, features):
        """处理有decision_function的模型"""
        decision_value = self.model.decision_function(features)
        
        if isinstance(decision_value, np.ndarray):
            decision_value = decision_value.flatten()[0]
        
        # 转换为概率
        prob1 = 1 / (1 + np.exp(-decision_value))
        probs = np.array([1 - prob1, prob1])
        pred = self.model.predict(features)[0]
        
        return pred, probs
    
    def _handle_basic_prediction(self, features):
        """处理基本预测模型"""
        pred = self.model.predict(features)[0]
        probs = np.array([0, 1]) if pred == 1 else np.array([1, 0])
        return pred, probs
    
    def predict_sample(self, file_path):
        """
        预测单个样本
        
        参数:
            file_path: 样本文件路径
            
        返回:
            dict: 预测结果字典，包含预测类别、概率、置信度等信息
        """
        if not self.load_model():
            return {"success": False, "error": "模型加载失败"}
        
        try:
            # 检测特征
            training_features, normalization_factor = self.feature_detector.detect_training_features()
            
            if training_features is None:
                return {"success": False, "error": "无法检测训练特征"}
            
            # 处理样本
            sample_features = self.feature_detector.process_prediction_sample(
                file_path, training_features, normalization_factor
            )
            
            # 预测
            prediction, probabilities = self.get_prediction_probability(sample_features)
            
            if prediction is None:
                return {"success": False, "error": "预测失败"}
            
            # 更新类别映射
            self._update_class_mapping()
            
            # 构建结果
            predicted_class = self.reverse_class_mapping.get(prediction, "未知")
            max_probability = max(probabilities)
            
            # 确定置信度等级
            if max_probability >= 0.7:
                confidence_level = "高"
                confidence_color = 'green'
            elif max_probability >= 0.5:
                confidence_level = "中等"
                confidence_color = 'blue'
            else:
                confidence_level = "低"
                confidence_color = 'orange'
            
            result = {
                "success": True,
                "predicted_class": predicted_class,
                "probabilities": probabilities,
                "class_names": list(self.reverse_class_mapping.values()),
                "confidence_level": confidence_level,
                "confidence_color": confidence_color,
                "max_probability": max_probability,
                "file_name": os.path.basename(file_path),
                "n_features": len(training_features),
                "normalization_factor": normalization_factor
            }
            
            log_message(f"预测完成 - 样本: {result['file_name']}, 结果: {predicted_class}", "SUCCESS")
            return result
            
        except Exception as e:
            error_msg = f"预测过程中发生错误: {str(e)}"
            log_message(error_msg, "ERROR")
            return {"success": False, "error": error_msg}
    
    def format_prediction_result(self, result):
        """
        格式化预测结果为显示文本
        
        参数:
            result: predict_sample返回的结果字典
            
        返回:
            str: 格式化的结果文本
        """
        if not result["success"]:
            return f"预测失败: {result['error']}"
        
        class_names = result["class_names"]
        probabilities = result["probabilities"]
        
        # 构建概率文本
        prob_text = f"{class_names[0]}={probabilities[0]:.4f}, {class_names[1]}={probabilities[1]:.4f}"
        
        # 构建完整结果文本
        result_text = f"预测结果: {result['predicted_class']}\n"
        result_text += f"类别概率: {prob_text}\n"
        result_text += f"置信度: {result['confidence_level']} ({result['max_probability']:.4f})\n"
        result_text += f"预测样本: {result['file_name']}\n"
        result_text += f"特征数量: {result['n_features']}\n"
        result_text += f"归一化因子: {result['normalization_factor']:.1f}"
        
        return result_text


class PredictionUI:
    """预测界面处理类"""
    
    def __init__(self, help_system=None):
        self.predictor = ModelPredictor()
        self.help_system = help_system
    
    def open_file_dialog(self, result_label):
        """
        打开文件选择对话框
        
        参数:
            result_label: 用于显示结果的标签控件
        """
        file_path = filedialog.askopenfilename(
            initialdir="/",
            title="选择要预测的文件",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if file_path:
            self.predict_and_display(file_path, result_label)
    
    def predict_and_display(self, file_path, result_label):
        """
        执行预测并显示结果
        
        参数:
            file_path: 样本文件路径
            result_label: 显示结果的标签控件
        """
        # 执行预测
        result = self.predictor.predict_sample(file_path)
        
        # 格式化并显示结果
        result_text = self.predictor.format_prediction_result(result)
        
        if result["success"]:
            result_label.configure(
                text=result_text,
                text_color=result["confidence_color"],
                font=ctk.CTkFont(size=12, weight="bold")
            )
            
            # 通知帮助系统
            if self.help_system:
                self.help_system.complete_step("predict_sample")
        else:
            result_label.configure(
                text=result_text,
                text_color='red'
            )
    
    def batch_predict(self, file_paths, progress_callback=None):
        """
        批量预测功能
        
        参数:
            file_paths: 文件路径列表
            progress_callback: 进度回调函数
            
        返回:
            list: 预测结果列表
        """
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            result = self.predictor.predict_sample(file_path)
            results.append(result)
            
            # 更新进度
            if progress_callback:
                progress = (i + 1) / total_files
                progress_callback(progress, f"预测进度: {i+1}/{total_files}")
        
        return results


# ========== 便捷函数接口（保持向后兼容）==========
def predict_unknown_sample(file_path, prediction_result_label, help_system=None):
    """
    便捷的预测函数 - 保持与原代码的兼容性
    
    参数:
        file_path: 样本文件路径
        prediction_result_label: 结果显示标签
        help_system: 帮助系统实例
        
    返回:
        tuple: (predicted_class, probabilities) 或 (None, None)
    """
    ui = PredictionUI(help_system)
    ui.predict_and_display(file_path, prediction_result_label)
    
    # 为了兼容性，也返回预测结果
    result = ui.predictor.predict_sample(file_path)
    if result["success"]:
        return result["predicted_class"], result["probabilities"]
    else:
        return None, None


def open_file_dialog(prediction_result_label, help_system=None):
    """
    便捷的文件对话框函数 - 保持与原代码的兼容性
    
    参数:
        prediction_result_label: 结果显示标签
        help_system: 帮助系统实例
    """
    ui = PredictionUI(help_system)
    ui.open_file_dialog(prediction_result_label)


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 示例1: 直接使用预测器
    predictor = ModelPredictor()
    result = predictor.predict_sample("sample.txt")
    print(predictor.format_prediction_result(result))
    
    # 示例2: 批量预测
    ui = PredictionUI()
    file_list = ["sample1.txt", "sample2.txt", "sample3.txt"]
    
    def progress_update(progress, message):
        print(f"{message} ({progress:.1%})")
    
    batch_results = ui.batch_predict(file_list, progress_update)