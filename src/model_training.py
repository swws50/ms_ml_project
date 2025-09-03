# model_training.py - 专门负责模型训练的模块（重构版）

# 标准库导入 
import os

# 第三方库导入 
import customtkinter as ctk
import numpy as np
import tqdm
from joblib import dump
from sklearn.cross_decomposition import PLSRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import (
    balanced_accuracy_score, confusion_matrix, 
    classification_report, roc_curve, auc
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from tkinter import messagebox

# 本地模块导入 
from config import MODEL_CONFIGS, OUTPUT_FILES, TRAINING_ITERATIONS, TEST_SIZE
import data_store
from utils import log_message, clear_log
from validation_decorators import require_data_store, safe_model_operation, log_execution_time
from visualization import visualize_performance


class ModelTrainer:
    """模型训练器类 - 统一管理训练相关功能"""
    
    def __init__(self):
        self.training_results = {}
        self.best_model = None
        self.best_score = -1
    
    def find_optimal_threshold(self, y_true, y_pred_proba):
        """
        基于ROC曲线分析寻找最优分类阈值
        
        参数:
            y_true: 真实类别标签
            y_pred_proba: 模型的连续预测值或概率估计
            
        返回:
            float: 最优分类阈值
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        optimal_idx = np.argmax(tpr - fpr)
        return thresholds[optimal_idx]
    
    def train_single_iteration(self, row, column, model_class, params):
        """
        执行单次训练迭代
        
        参数:
            row: 特征数据
            column: 标签数据
            model_class: 模型类
            params: 模型参数
            
        返回:
            dict: 本次迭代的结果
        """
        # 划分训练测试集
        train_X, test_X, train_y, test_y = train_test_split(
            row, column, test_size=TEST_SIZE, stratify=column
        )
        
        # 训练模型
        current_model = model_class(**params)
        current_model.fit(train_X, train_y)
        
        # 预测处理
        if isinstance(current_model, PLSRegression):
            # PLS回归需要特殊处理
            train_pred_raw = current_model.predict(train_X).flatten()
            test_pred_raw = current_model.predict(test_X).flatten()
            
            optimal_threshold = self.find_optimal_threshold(train_y, train_pred_raw)
            
            train_y_pred = (train_pred_raw > optimal_threshold).astype(int)
            test_y_pred = (test_pred_raw > optimal_threshold).astype(int)
            
            threshold_used = optimal_threshold
        else:
            train_y_pred = current_model.predict(train_X)
            test_y_pred = current_model.predict(test_X)
            threshold_used = None
        
        # 性能评估
        fpr, tpr, thresholds = roc_curve(test_y, test_y_pred)
        auc_score = auc(fpr, tpr)
        
        train_acc = balanced_accuracy_score(train_y, train_y_pred)
        test_acc = balanced_accuracy_score(test_y, test_y_pred)
        
        # 混淆矩阵和F分数
        cm = confusion_matrix(test_y, test_y_pred).flatten()
        fscore_dict = classification_report(test_y, test_y_pred, labels=[0, 1], output_dict=True)
        
        fscores = [
            fscore_dict["weighted avg"]["precision"],
            fscore_dict["weighted avg"]["recall"],
            fscore_dict["weighted avg"]["f1-score"],
            0  # 预留位置
        ]
        
        return {
            'model': current_model,
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'confusion_matrix': cm,
            'fscores': fscores,
            'fpr': fpr,
            'tpr': tpr,
            'roc_thresholds': thresholds,
            'auc': auc_score,
            'threshold_used': threshold_used
        }
    
    def train_model(self, model_name, progress_callback=None):
        """
        执行完整的模型训练流程
        
        参数:
            model_name: 模型名称
            progress_callback: 进度回调函数 callback(progress, message)
            
        返回:
            dict: 训练结果
        """
        # 获取训练数据
        row, column, df = data_store.get_training_data()
        log_message(f"获取训练数据: {row.shape}", "INFO")
        
        # 获取模型类和参数
        if model_name not in MODEL_CONFIGS:
            raise ValueError(f"未知的模型: {model_name}")
        
        model_class = globals()[model_name]
        params = MODEL_CONFIGS[model_name]
        
        # 初始化结果存储
        results = {
            'balanced_accuracy_train': [],
            'balanced_accuracy_test': [],
            'trained_models': [],
            'fpr_list': [],
            'tpr_list': [],
            'thresholds_list': [],
            'auc_list': [],
            'Fscores': np.zeros((TRAINING_ITERATIONS, 4)),
            'thresholds_used': [],
            'confusion_matrixs': np.zeros((TRAINING_ITERATIONS, 4))
        }
        
        self.best_score = -1
        self.best_model = None
        
        log_message(f"开始{TRAINING_ITERATIONS}轮训练循环...")
        
        # 主训练循环
        for i in range(TRAINING_ITERATIONS):
            # 执行单次训练
            iteration_result = self.train_single_iteration(row, column, model_class, params)
            
            # 收集结果
            results['balanced_accuracy_train'].append(iteration_result['train_accuracy'])
            results['balanced_accuracy_test'].append(iteration_result['test_accuracy'])
            results['trained_models'].append(iteration_result['model'])
            results['fpr_list'].append(iteration_result['fpr'])
            results['tpr_list'].append(iteration_result['tpr'])
            results['thresholds_list'].append(iteration_result['roc_thresholds'])
            results['auc_list'].append(iteration_result['auc'])
            results['Fscores'][i] = iteration_result['fscores']
            results['confusion_matrixs'][i] = iteration_result['confusion_matrix']
            
            if iteration_result['threshold_used'] is not None:
                results['thresholds_used'].append(iteration_result['threshold_used'])
            
            # 更新最佳模型
            test_acc = iteration_result['test_accuracy']
            if test_acc > self.best_score:
                self.best_score = test_acc
                self.best_model = iteration_result['model']
                log_message(f"发现更高分数：{self.best_score:.4f} (迭代{i+1})")
            
            # 更新进度
            if progress_callback:
                progress = (i + 1) / TRAINING_ITERATIONS
                progress_callback(progress, f'分析进度: {progress:.1%}')
        
        log_message(f"训练完成！最优模型分数：{self.best_score:.4f}")
        
        # 保存最佳模型
        log_message("最佳模型已保存到数据存储模块", "SUCCESS")
        
        # 保存训练结果
        self.save_training_results(results)
        
        self.training_results = results
        return results
    
    def save_training_results(self, results):
        """保存训练结果到文件"""
        log_message("保存训练结果文件...")
        
        try:
            # 保存各种指标
            np.savetxt(OUTPUT_FILES['confusion_matrix'], results['confusion_matrixs'], delimiter=",")
            np.savetxt(OUTPUT_FILES['fscore'], results['Fscores'], delimiter=",")
            np.savetxt(OUTPUT_FILES['auc'], results['auc_list'], delimiter=",")
            np.save(OUTPUT_FILES['fpr_values'], np.array(results['fpr_list'], dtype=object))
            np.save(OUTPUT_FILES['tpr_values'], np.array(results['tpr_list'], dtype=object))
            np.save(OUTPUT_FILES['thresholds_values'], np.array(results['thresholds_list'], dtype=object))
            
            # 保存最佳模型
            if self.best_model is not None:
                from datetime import datetime
                from config import output_manager
                
                # 生成带时间戳的文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_type = type(self.best_model).__name__
                norm_status = "normalized" if data_store.is_normalization_enabled() else "raw"
                
                filename = f"{model_type}_{norm_status}_{timestamp}.joblib"
                model_path = output_manager.get_path('model', filename)
                
                # 保存模型
                dump(self.best_model, model_path)
                 # 设置为最新训练的模型（用于预测时的默认选择）
                data_store.set_latest_trained_model(self.best_model, model_path)
                
                log_message(f"模型已保存: {filename}")
                log_message(f"测试集分数: {self.best_score:.4f}")
            
            # 保存PLS阈值（如果存在）
            if len(results['thresholds_used']) > 0:
                np.savetxt(OUTPUT_FILES['pls_thresholds'], results['thresholds_used'], delimiter=",")
                mean_threshold = np.mean(results['thresholds_used'])
                log_message(f"PLS回归平均最优阈值: {mean_threshold:.4f}")
                
        except Exception as e:
            log_message(f"保存训练结果失败: {str(e)}", "ERROR")
    
    def get_training_summary(self):
        """
        获取训练结果摘要
        
        返回:
            dict: 训练摘要信息
        """
        if not self.training_results:
            return {"error": "尚未完成训练"}
        
        results = self.training_results
        
        return {
            "best_score": self.best_score,
            "mean_train_accuracy": np.mean(results['balanced_accuracy_train']),
            "mean_test_accuracy": np.mean(results['balanced_accuracy_test']),
            "mean_auc": np.mean(results['auc_list']),
            "n_iterations": len(results['balanced_accuracy_test']),
            "model_type": type(self.best_model).__name__ if self.best_model else None,
            "has_thresholds": len(results['thresholds_used']) > 0
        }


class TrainingUI:
    """训练界面处理类"""
    
    def __init__(self, help_system=None):
        self.trainer = ModelTrainer()
        self.help_system = help_system
    
    def train_with_ui_feedback(self, model_name, progress_label, progress_bar, 
                             train_label, test_label, status_label, root):
        """
        带UI反馈的训练函数
        
        参数:
            model_name: 模型名称
            progress_label: 进度标签
            progress_bar: 进度条
            train_label: 训练结果标签
            test_label: 测试结果标签
            status_label: 状态标签
            root: 根窗口
        """
        def progress_callback(progress, message):
            # 检查终止标志
            if hasattr(root, 'gui_manager') and root.gui_manager._operation_cancelled:
                raise InterruptedError("操作被用户终止")
            
            # 原有的UI更新逻辑
            if progress_label:
                progress_label.configure(text=message)
            if progress_bar:
                progress_bar.set(progress)
            if root:
                root.update_idletasks()
                root.update()
        
        try:
            # 清空日志
            log_message("=> 开始模型训练...")
            log_message(f"使用模型: {model_name}")
            
            # 执行训练
            results = self.trainer.train_model(model_name, progress_callback)
            
            # 更新UI显示
            summary = self.trainer.get_training_summary()
            train_label.configure(text=f"平均训练集平衡精度: {summary['mean_train_accuracy']:.4f}")
            test_label.configure(text=f"平均测试集平衡精度: {summary['mean_test_accuracy']:.4f}")
            status_label.configure(
                text=f'模型保存状态: 已保存 (分数: {summary["best_score"]:.4f})', 
                text_color='green'
            )
            
            log_message(f"平均训练集平衡精度: {summary['mean_train_accuracy']:.4f}")
            log_message(f"平均测试集平衡精度: {summary['mean_test_accuracy']:.4f}")
            log_message("开始生成可视化图表...")
            
            # 推进步骤
            if self.help_system:
                self.help_system.advance_step("view_results")
            
            # 生成可视化
            thresholds = results['thresholds_used'] if len(results['thresholds_used']) > 0 else None
            visualize_performance(
                results['balanced_accuracy_train'],
                results['balanced_accuracy_test'],
                results['Fscores'],
                results['confusion_matrixs'],
                results['fpr_list'],
                results['tpr_list'],
                results['auc_list'],
                thresholds,
                root
            )
            
            log_message("所有任务完成！")

        except InterruptedError:
            log_message("训练过程被终止", "WARNING")
            status_label.configure(text='模型保存状态: 训练被终止', text_color='orange')
            if progress_bar:
                progress_bar.set(0)
                    
        except Exception as e:
            error_msg = f"训练过程中出现错误: {str(e)}"
            log_message(error_msg, "ERROR")
            messagebox.showerror("训练错误", f"模型训练时出现错误：{str(e)}")
            if progress_bar:  # 添加空值检查
                progress_bar.set(0)
            status_label.configure(text='模型保存状态: 训练失败', text_color='red')



# 使用示例 
if __name__ == "__main__":
    # 示例1: 直接使用训练器
    trainer = ModelTrainer()
    
    def simple_progress(progress, message):
        print(f"{message} ({progress:.1%})")
    
    # 假设数据已加载到data_store
    results = trainer.train_model("PLSRegression", simple_progress)
    summary = trainer.get_training_summary()
    print(f"训练摘要: {summary}")
    
    # 示例2: 使用UI训练器
    # ui = TrainingUI()
    # ui.train_with_ui_feedback("PLSRegression", ...)