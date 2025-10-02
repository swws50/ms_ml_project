# model_predictor.py - 统一的预测管理模块（合并版）

# 标准库导入 
import os

# 第三方库导入 
import customtkinter as ctk
import numpy as np
import pandas as pd
from joblib import load
from sklearn.cross_decomposition import PLSRegression
from tkinter import filedialog, messagebox
from datetime import datetime

# 本地模块导入 
from config import OUTPUT_FILES, MZ_TOLERANCE, get_class_mapping
import data_store
from feature_detector import FeatureDetector
from utils import log_message
from validation_decorators import require_data_store, safe_model_operation


class PredictionManager:
    """预测管理器 - 统一管理预测、模型信息、UI的完整功能"""
    
    def __init__(self, help_system=None):
        self.help_system = help_system
        self.model = None
        self.feature_detector = FeatureDetector()
        self.class_mapping = {}
        self.reverse_class_mapping = {}
        self.info_window = None  # 模型信息窗口引用
        self._update_class_mapping()
    
    def _update_class_mapping(self):
        """更新类别映射"""
        self.class_mapping, self.reverse_class_mapping = get_class_mapping()
    
    # 模型加载相关 
    def load_model(self):
        """智能加载模型"""
        try:
            # 1. 优先使用用户手动选择的模型
            if hasattr(self, 'temp_model_path') and self.temp_model_path:
                self.model = load(self.temp_model_path)
                log_message(f"使用用户选择的模型: {os.path.basename(self.temp_model_path)}", "INFO")
                return True
            
            # 2. 使用最新训练的模型（内存中）
            latest_model, latest_path = data_store.get_latest_trained_model()
            if latest_model is not None:
                self.model = latest_model
                log_message("使用最新训练的模型（内存中）", "INFO")
                return True
            
            # 3. 从最新的模型文件加载（如果内存中没有）
            if latest_path and os.path.exists(latest_path):
                self.model = load(latest_path)
                log_message(f"从最新模型文件加载: {os.path.basename(latest_path)}", "INFO")
                return True
            
            # 4. 扫描模型目录，找到最新的模型文件
            model_dir = "output/models"  # 根据实际路径调整
            if os.path.exists(model_dir):
                model_files = [f for f in os.listdir(model_dir) if f.endswith('.joblib')]
                if model_files:
                    # 按时间戳排序，选择最新的
                    latest_file = max(model_files)
                    latest_model_path = os.path.join(model_dir, latest_file)
                    self.model = load(latest_model_path)
                    log_message(f"自动选择最新模型文件: {latest_file}", "INFO")
                    return True
            
            log_message("未找到可用的模型文件", "ERROR")
            return False
            
        except Exception as e:
            log_message(f"加载模型失败: {str(e)}", "ERROR")
            self.model = None
            return False
    
    # 预测功能相关 
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
        
        # 转换为概率，避免数值溢出
        diff = (raw_value - threshold) * 10
        diff = np.clip(diff, -500, 500)  # 限制范围避免溢出
        prob1 = 1 / (1 + np.exp(-diff))
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
            training_features, normalization_factor = self.feature_detector.load_training_features()
            
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
        
        # 获取归一化状态
        norm_status = "已归一化" if data_store.is_normalization_enabled() else "原始数据"
        norm_factor = result['normalization_factor']

        # 构建完整结果文本
        result_text = f"预测结果: {result['predicted_class']}\n"
        result_text += f"类别概率: {prob_text}\n"
        result_text += f"置信度: {result['confidence_level']} ({result['max_probability']:.4f})\n"
        result_text += f"预测样本: {result['file_name']}\n"
        result_text += f"特征数量: {result['n_features']}\n"
        result_text += f"数据模式: {norm_status}"
        # 只在归一化启用时显示归一化因子
        if data_store.is_normalization_enabled() and norm_factor:
            result_text += f"\n归一化因子: {norm_factor:.1f}"
            
        return result_text
    
    # UI交互相关 
    def open_file_dialog(self, result_label):
        """打开文件选择对话框"""
        file_paths = filedialog.askopenfilenames(
            initialdir="/",
            title="选择要预测的文件(可多选)",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        # 用户取消选择时直接返回
        if not file_paths:
            return
        
        # 清空之前的所有结果
        result_label.delete("1.0", "end")
        
        # 遍历所有文件
        for i, file_path in enumerate(file_paths, 1):
            if i > 1:
                result_label.insert("end", "\n" + "="*50 + "\n")
            result_label.insert("end", f"【样本 {i}】\n")
            
            result = self.predict_sample(file_path)
            result_text = self.format_prediction_result(result)
            result_label.insert("end", result_text + "\n")
            
            # 设置颜色
            if result.get("success"):
                result_label.configure(text_color=result.get("confidence_color", "black"))
            else:
                result_label.configure(text_color='red')
    
    def predict_and_display(self, file_path, result_label):
        """
        执行预测并显示结果
        
        参数:
            file_path: 样本文件路径
            result_label: 显示结果的标签控件
        """
        # 执行预测
        result = self.predict_sample(file_path)
        
        # 格式化并显示结果
        result_text = self.format_prediction_result(result)
        
        if result["success"]:
            result_label.delete("1.0", "end")
            result_label.insert("1.0", result_text)
            result_label.configure(text_color=result["confidence_color"])
            
            # 通知帮助系统
            if self.help_system:
                self.help_system.complete_step("predict_sample")
        else:
            result_label.delete("1.0", "end")
            result_label.insert("1.0", result_text)
            result_label.configure(text_color='red')
        # 保存最新预测结果到data_store    
        prediction_data = {
            "filename": result.get("file_name", ""),
            "predicted_class": result.get("predicted_class", ""),
            "confidence": result.get("max_probability", 0),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data_store.set_latest_prediction(prediction_data)
        
    # 模型信息相关（从model_info.py迁移过来）
    def get_model_info(self):
        """
        获取模型详细信息
        
        返回:
            dict: 模型信息字典
        """
        if self.model is None:
            self.load_model()
            if not self.load_model():
                return {"error": "模型未加载"}
        
        info = {
            "model_type": type(self.model).__name__,
            "parameters": self.model.get_params(),
            "special_info": self._get_special_model_info()
        }
        
        return info
    
    def _get_special_model_info(self):
        """获取特定模型类型的特殊信息"""
        special_info = {}
        
        if hasattr(self.model, 'feature_importances_'):
            # 特征重要性
            importances = self.model.feature_importances_
            special_info["feature_importances"] = {
                "values": importances,
                "top_5": self._get_top_features(importances, 5)
            }
        
        elif hasattr(self.model, 'coef_'):
            # 模型系数
            coefs = self.model.coef_
            
            if isinstance(self.model, PLSRegression):
                special_info.update(self._get_pls_info())
            else:
                special_info["coefficients"] = coefs
        
        return special_info
    
    def _get_pls_info(self):
        """获取PLS回归特有信息"""
        pls_info = {
            "n_components": self.model.n_components
        }
        
        if hasattr(self.model, 'x_weights_'):
            weights = self.model.x_weights_
            pls_info["x_weights_shape"] = weights.shape
            pls_info["top_weights"] = self._format_matrix_preview(weights, "权重")
        
        if hasattr(self.model, 'x_loadings_'):
            loadings = self.model.x_loadings_
            pls_info["x_loadings_shape"] = loadings.shape
            pls_info["top_loadings"] = self._format_matrix_preview(loadings, "载荷")
        
        return pls_info
    
    def _format_matrix_preview(self, matrix, name, max_features=5, max_components=3):
        """格式化矩阵预览"""
        preview = {}
        n_features = min(max_features, matrix.shape[0])
        n_components = min(max_components, matrix.shape[1])
        
        for i in range(n_features):
            feature_values = []
            for j in range(n_components):
                feature_values.append(f"{matrix[i, j]:.4f}")
            preview[f"特征_{i+1}"] = ", ".join(feature_values)
        
        return preview
    
    def _get_top_features(self, importances, top_n=5):
        """获取top特征重要性"""
        if len(importances) == 0:
            return {}
        
        # 获取排序索引
        sorted_indices = importances.argsort()[::-1][:top_n]
        
        top_features = {}
        for rank, idx in enumerate(sorted_indices, 1):
            top_features[f"特征_{idx+1}"] = f"{importances[idx]:.4f}"
        
        return top_features
    
    def format_info_text(self, info):
        """
        将模型信息格式化为显示文本
        
        参数:
            info: get_model_info返回的信息字典
            
        返回:
            str: 格式化的文本
        """
        if "error" in info:
            return f"错误: {info['error']}"
        
        text_lines = []
        
        # 基本信息
        text_lines.append(f"模型类型: {info['model_type']}\n")
        
        # 参数信息
        text_lines.append("模型参数:")
        for param_name, param_value in info['parameters'].items():
            text_lines.append(f"- {param_name}: {param_value}")
        
        # 特殊信息
        special_info = info.get('special_info', {})
        
        if 'feature_importances' in special_info:
            text_lines.append("\n特征重要性 (Top 5):")
            for feature, importance in special_info['feature_importances']['top_5'].items():
                text_lines.append(f"- {feature}: {importance}")
        
        elif 'n_components' in special_info:
            text_lines.append(f"\nPLS回归特有信息:")
            text_lines.append(f"- 组件数: {special_info['n_components']}")
            
            if 'top_weights' in special_info:
                text_lines.append("\nX权重 (前5个特征的前3个组件):")
                for feature, weights in special_info['top_weights'].items():
                    text_lines.append(f"- {feature}: {weights}")
            
            if 'top_loadings' in special_info:
                text_lines.append("\nX载荷 (前5个特征的前3个组件):")
                for feature, loadings in special_info['top_loadings'].items():
                    text_lines.append(f"- {feature}: {loadings}")
        
        elif 'coefficients' in special_info:
            coefs = special_info['coefficients']
            if coefs.ndim == 1:
                text_lines.append(f"\n特征系数 (前5个):")
                for i in range(min(5, len(coefs))):
                    text_lines.append(f"- 特征 {i+1}: {coefs[i]:.4f}")
            else:
                text_lines.append(f"\n多类别系数矩阵形状: {coefs.shape}")
        
        return "\n".join(text_lines)
    
    def show_model_info_window(self, parent=None, model_path=None):
        """显示模型信息窗口"""
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.lift()
            self.info_window.focus_force()
            return
        
        # 如果指定了模型路径，临时加载该模型
        original_model = self.model
        if model_path:
            try:
                self.model = load(model_path)
                log_message(f"临时加载模型用于信息查看: {os.path.basename(model_path)}", "INFO")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载指定模型: {str(e)}")
                return
        
        info = self.get_model_info()
        
        # 恢复原模型
        if model_path:
            self.model = original_model
        
        if "error" in info:
            messagebox.showerror("错误", info["error"])
            return
        
        # 创建窗口的代码保持不变...
        self.info_window = ctk.CTkToplevel(parent)
        model_name = os.path.basename(model_path) if model_path else info['model_type']
        self.info_window.title(f"模型信息: {model_name}")
        self.info_window.geometry("600x400")
        
        self._setup_info_window_properties()
        
        info_text = ctk.CTkTextbox(self.info_window, width=580, height=360)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        formatted_text = self.format_info_text(info)
        info_text.insert("end", formatted_text)
        
        log_message("模型信息窗口已打开", "INFO")

    def _setup_info_window_properties(self):
        """设置信息窗口属性"""
        # 强力置顶方案
        self.info_window.attributes('-topmost', True)
        self.info_window.focus_force()
        self.info_window.lift()
        self.info_window.tkraise()
        self.info_window.grab_set()  # 模态窗口
        
        # 延迟取消置顶
        self.info_window.after(1000, lambda: self.info_window.attributes('-topmost', False))
        
        # 窗口关闭处理
        def on_closing():
            self.info_window.grab_release()
            self.info_window.destroy()
            self.info_window = None
        
        self.info_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    def close_info_window(self):
        """关闭模型信息窗口"""
        try:
            if self.info_window and self.info_window.winfo_exists():
                self.info_window.grab_release()  # 释放模态
                self.info_window.destroy()
                self.info_window = None
                log_message("模型信息窗口已关闭", "INFO")
                return True
        except Exception as e:
            log_message(f"关闭模型信息窗口时出错: {e}", "WARNING")
            self.info_window = None
        return False

    # 批量预测相关（为步骤2准备）
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
            result = self.predict_sample(file_path)
            results.append(result)
            
            # 更新进度
            if progress_callback:
                progress = (i + 1) / total_files
                progress_callback(progress, f"预测进度: {i+1}/{total_files}")
        
        return results

    def scan_available_models(self, model_directory="models"):
        """扫描可用的模型文件"""
        available_models = ["自动检测"]  # 默认选项
        
        # 检查模型目录
        if os.path.exists(model_directory):
            for file in os.listdir(model_directory):
                if file.endswith('.joblib'):
                    model_name = os.path.splitext(file)[0]  # 去掉扩展名
                    available_models.append(model_name)
        
        # 检查默认的best_model.joblib
        if os.path.exists(OUTPUT_FILES['best_model']):
            available_models.append("最近训练模型")
        
        return available_models

    def load_specific_model(self, model_name):
        """加载指定的模型"""
        if model_name == "自动检测":
            return self.load_model()  # 使用现有逻辑
        elif model_name == "最近训练模型":
            return self.load_model()  # 使用现有逻辑
        else:
            # 加载指定的模型文件
            model_path = f"models/{model_name}.joblib"
            try:
                self.model = load(model_path)
                log_message(f"已加载模型: {model_name}", "INFO")
                return True
            except Exception as e:
                log_message(f"加载模型失败 {model_name}: {str(e)}", "ERROR")
                return False



# 使用示例 
if __name__ == "__main__":
    # 示例1: 直接使用统一管理器
    manager = PredictionManager()
    result = manager.predict_sample("sample.txt")
    print(manager.format_prediction_result(result))
    
    # 示例2: 批量预测
    file_list = ["sample1.txt", "sample2.txt", "sample3.txt"]
    
    def progress_update(progress, message):
        print(f"{message} ({progress:.1%})")
    
    batch_results = manager.batch_predict(file_list, progress_update)
    
    # 示例3: 查看模型信息
    info = manager.get_model_info()
    formatted_info = manager.format_info_text(info)
    print(formatted_info)