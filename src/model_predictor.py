# model_predictor.py - 统一的预测管理模块（合并版）

# 标准库导入 
import os
import csv

# 第三方库导入 
import customtkinter as ctk
import numpy as np
import pandas as pd
from joblib import load
from sklearn.cross_decomposition import PLSRegression
from tkinter import filedialog, messagebox
from datetime import datetime

# 本地模块导入 
from config import MZ_TOLERANCE
import data_store
from data_store import class_manager
from data_processing import FeatureDetector
from utils import log_message, set_window_icon, center_window


class PredictionManager:
    """预测管理器 - 统一管理预测、模型信息、UI的完整功能"""
    
    def __init__(self, help_system=None):
        self.help_system = help_system
        self.model = None
        self.feature_detector = FeatureDetector()
        self.info_window = None  # 模型信息窗口引用
    
    # 模型加载相关
    def reset(self):
        """清空预测器状态（重置时调用）"""
        self.model = None
        self.temp_model_path = None
        self.feature_detector.training_features = None
        self.feature_detector.normalization_method = None

    def _apply_loaded(self, loaded, source_label: str):
        """解包 joblib bundle：{"model": ..., "training_features": [...], "normalization_method": ...}"""
        if not (isinstance(loaded, dict) and "model" in loaded):
            raise ValueError("模型格式不兼容，请使用当前版本重新训练以生成 bundle 文件")

        self.model = loaded["model"]
        features = loaded.get("training_features") or []
        norm = loaded.get("normalization_method")
        self.pls_threshold = loaded.get("pls_threshold", None)
        self.feature_detector.training_features = features if features else None
        self.feature_detector.normalization_method = norm
        log_message(f"{source_label}", "INFO")

    def load_model(self):
        """智能加载模型"""
        try:
            # 1. 优先使用用户手动选择的模型
            if hasattr(self, 'temp_model_path') and self.temp_model_path:
                self._apply_loaded(
                    load(self.temp_model_path),
                    f"使用用户选择的模型: {os.path.basename(self.temp_model_path)}"
                )
                return True

            # 2. 从最新的模型文件加载（含当前会话刚训练完的模型）
            _, latest_path = data_store.get_latest_trained_model()
            if latest_path and os.path.exists(latest_path):
                self._apply_loaded(
                    load(latest_path),
                    f"从最新模型文件加载: {os.path.basename(latest_path)}"
                )
                return True

            # 3. 扫描模型目录，找到最新的模型文件
            model_dir = "output/models"
            if os.path.exists(model_dir):
                model_files = [f for f in os.listdir(model_dir) if f.endswith('.joblib')]
                if model_files:
                    latest_file = max(model_files)
                    latest_model_path = os.path.join(model_dir, latest_file)
                    self._apply_loaded(
                        load(latest_model_path),
                        f"自动选择最新模型文件: {latest_file}"
                    )
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
        
        # 获取最优阈值（从模型bundle中读取）
        if hasattr(self, 'pls_threshold') and self.pls_threshold is not None:
            threshold = self.pls_threshold
        else:
            threshold = 0.5
            log_message("模型bundle中未找到PLS阈值，使用默认阈值0.5", "WARNING")
        
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
            training_features, normalization_method = self.feature_detector.load_training_features()
            
            if training_features is None:
                return {"success": False, "error": "无法检测训练特征"}
            
            # 处理样本
            sample_features = self.feature_detector.process_prediction_sample(
                file_path, training_features, normalization_method
            )
            
            # 预测
            prediction, probabilities = self.get_prediction_probability(sample_features)
            
            if prediction is None:
                return {"success": False, "error": "预测失败"}
            
            # 更新类别映射
            predicted_class = class_manager.decode(prediction)
            
            # 构建结果
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
                "class_names": list(class_manager.names),
                "confidence_level": confidence_level,
                "confidence_color": confidence_color,
                "max_probability": max_probability,
                "file_name": os.path.basename(file_path),
                "n_features": len(training_features),
                "normalization_method": normalization_method
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
        
        # 单个文件：直接预测显示
        if len(file_paths) == 1:
            self.predict_and_display(file_paths[0], result_label)
            return
        
        # 批量预测
        log_message(f"开始批量预测 {len(file_paths)} 个文件...", "INFO")
        results = []
        
        for i, file_path in enumerate(file_paths, 1):
            result = self.predict_sample(file_path)
            results.append(result)
            
            # 在界面上逐个显示每个预测结果（保持原版样式）
            if i > 1:
                result_label.insert("end", "\n" + "-"*180 + "\n")
            result_label.insert("end", f"【样本 {i}】\n")
            
            result_text = self.format_prediction_result(result)
            result_label.insert("end", result_text + "\n")
            
            # 设置颜色
            if result.get("success"):
                result_label.configure(text_color=result.get("confidence_color", "black"))
            else:
                result_label.configure(text_color='red')
        
        # 自动导出CSV（静默导出，不打断用户查看结果）
        csv_path = self.export_batch_results_to_csv(results)
        if csv_path:
            log_message(f"批量预测结果已导出: {csv_path}", "SUCCESS")
            
            # 在界面底部添加导出提示
            result_label.insert("end", "\n" + "="*80 + "\n")
            result_label.insert("end", f"✓ 结果已自动导出至:\n{csv_path}\n")
            
        
    def export_batch_results_to_csv(self, results, output_path=None):
        """
        将批量预测结果导出为CSV（Excel可打开）
        
        参数:
            results: batch_predict返回的结果列表
            output_path: 输出文件路径，None则自动生成
            
        返回:
            str: 保存的文件路径
        """
        if not output_path:
            from output_manager import output_manager
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            predictions_dir = output_manager.get_path('prediction', '')
            output_path = os.path.join(predictions_dir, f"batch_prediction_{timestamp}.csv")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 获取模型信息
        model_info = self._get_model_summary()
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入报告标题
                writer.writerow(['批量预测结果报告'])
                writer.writerow([])
                
                # 基本信息部分
                writer.writerow(['基本信息'])
                writer.writerow(['预测时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['样本总数', len(results)])
                writer.writerow([])
                
                # 模型信息部分
                writer.writerow(['模型信息'])
                writer.writerow(['模型类型', model_info['type']])
                writer.writerow(['模型来源', model_info['source']])
                if model_info.get('trained_time'):
                    writer.writerow(['训练时间', model_info['trained_time']])
                writer.writerow([])
                
                # 预测结果表格
                writer.writerow(['预测结果明细'])
                writer.writerow(['序号', '样本文件', '预测类别', '置信度等级', '最大概率', 
                             '为0类概率', '为1类概率', '特征数', ''])# 最后一列为预测状态列
                
                # 写入数据
                for i, result in enumerate(results, 1):
                    if result.get('success'):
                        probs = result['probabilities']
                        class_names = result['class_names']
                        
                        writer.writerow([
                            i,
                            result['file_name'],
                            result['predicted_class'],
                            result['confidence_level'],
                            f"{result['max_probability']:.4f}",
                            f"{probs[0]:.4f}",
                            f"{probs[1]:.4f}",
                            result['n_features'],
                            ''  # 成功时状态为空
                        ])
                    else:
                        # 失败时只在状态列显示错误信息
                        writer.writerow([
                            i,
                            result.get('file_name', '未知'),
                            '-',
                            '-',
                            '-',
                            '-',
                            '-',
                            '-',
                            '-',
                            '-',
                            result.get('error', '未知错误')  # 错误信息
                        ])
            
            return output_path
            
        except Exception as e:
            log_message(f"导出CSV失败: {str(e)}", "ERROR")
            return None

    def _get_model_summary(self):
        """
        获取模型摘要信息用于CSV导出
        
        返回:
            dict: 包含模型类型、来源等信息
        """
        model_summary = {
            'type': '未知',
            'source': '未知',
            'trained_time': None
        }
        
        try:
            if self.model is not None:
                model_summary['type'] = type(self.model).__name__
                
                # 判断模型来源
                if hasattr(self, 'temp_model_path') and self.temp_model_path:
                    model_summary['source'] = f"用户选择: {os.path.basename(self.temp_model_path)}"
                    # 尝试获取文件修改时间
                    if os.path.exists(self.temp_model_path):
                        import time
                        mtime = os.path.getmtime(self.temp_model_path)
                        model_summary['trained_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                else:
                    # 检查是否是最新训练的模型
                    latest_model, latest_path = data_store.get_latest_trained_model()
                    if latest_model is not None and self.model is latest_model:
                        model_summary['source'] = '最新训练模型（内存）'
                        model_summary['trained_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    elif latest_path:
                        model_summary['source'] = f"文件加载: {os.path.basename(latest_path)}"
                        if os.path.exists(latest_path):
                            import time
                            mtime = os.path.getmtime(latest_path)
                            model_summary['trained_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                    else:
                        model_summary['source'] = '自动检测'
            
        except Exception as e:
            log_message(f"获取模型信息时出错: {str(e)}", "WARNING")
        
        return model_summary

    def batch_predict(self, file_paths, progress_callback=None):
        """
        批量预测功能（修改版，返回结果）
        
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
            "special_info": self._get_special_model_info(),
            # bundle 元数据
            "n_training_features": len(self.feature_detector.training_features) if self.feature_detector.training_features else 0,
            "normalization_method": self.feature_detector.normalization_method,
            "pls_threshold": getattr(self, "pls_threshold", None),
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
        text_lines.append(f"模型类型: {info['model_type']}")

        # bundle 元数据
        n_feat = info.get("n_training_features", 0)
        norm = info.get("normalization_method") or "无"
        text_lines.append(f"训练特征数: {n_feat}")
        text_lines.append(f"归一化方法: {norm}")
        pls_thr = info.get("pls_threshold")
        if pls_thr is not None:
            text_lines.append(f"PLS 决策阈值: {pls_thr:.4f}")
        text_lines.append("")

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
        
        # 如果指定了模型路径，临时加载该模型（需保存并还原完整 bundle 状态）
        saved_state = None
        if model_path:
            saved_state = {
                "model": self.model,
                "training_features": self.feature_detector.training_features,
                "normalization_method": self.feature_detector.normalization_method,
                "pls_threshold": getattr(self, "pls_threshold", None),
            }
            try:
                self._apply_loaded(
                    load(model_path),
                    f"将临时加载模型用于信息查看"
                )
            except Exception as e:
                messagebox.showerror("错误", f"无法加载指定模型: {str(e)}")
                return

        info = self.get_model_info()

        # 恢复原完整状态
        if saved_state is not None:
            self.model = saved_state["model"]
            self.feature_detector.training_features = saved_state["training_features"]
            self.feature_detector.normalization_method = saved_state["normalization_method"]
            self.pls_threshold = saved_state["pls_threshold"]
        
        if "error" in info:
            messagebox.showerror("错误", info["error"])
            return
        
        # 创建窗口的代码保持不变...
        self.info_window = ctk.CTkToplevel(parent)
        model_name = os.path.basename(model_path) if model_path else info['model_type']
        self.info_window.title(f"模型信息: {model_name}")
        center_window(self.info_window, 600, 400)
        
        self._setup_info_window_properties()
        
        info_text = ctk.CTkTextbox(self.info_window, width=580, height=360)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        formatted_text = self.format_info_text(info)
        info_text.insert("end", formatted_text)
        
        log_message("模型信息窗口已打开", "INFO")

    def _setup_info_window_properties(self):
        """设置信息窗口属性"""
        set_window_icon(self.info_window)
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