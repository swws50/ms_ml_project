# model_training.py - 专门负责模型训练的模块（重构版）

# 标准库导入 
import os

# 第三方库导入 
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
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from tkinter import messagebox

# 本地模块导入 
from config import CROSS_VALIDATOR, CV_SPLITS, CV_REPEATS
from config import MODEL_CONFIGS, OUTPUT_FILES,  TEST_SIZE
import data_store
from utils import log_message, clear_log
from validation_decorators import log_execution_time
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
    
    
    def train_model(self, model_name, progress_callback=None):
        """
        使用嵌套交叉验证执行完整的模型训练流程
        
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

        if model_name == "LogisticRegressionCV" and "cv_shuffle" in params:
            params = params.copy()
            params["cv"] = StratifiedKFold(n_splits=params.pop("cv", 5), shuffle=params.pop("cv_shuffle", True))
        
        # 初始化结果存储
        results = {
            'train_accuracy': [],
            'test_accuracy': [],
            'trained_models': [],
            'fpr_values': [],
            'tpr_values': [],
            'thresholds_list': [],
            'auc_list': [],
            'f_scores': [],
            'thresholds_used': [],
            'confusion_matrices': []
        }
        
        self.best_score = -1
        self.best_model = None
        
        # 计算总折数
        total_folds = CROSS_VALIDATOR.get_n_splits(row, column)
        log_message(f"开始交叉验证训练 (总共{total_folds}折)...")
        
        # 交叉验证主循环
        fold_idx = 0
        for train_idx, test_idx in CROSS_VALIDATOR.split(row, column):
            fold_idx += 1
            
            # 获取当前折的数据
            train_X = row[train_idx]
            test_X = row[test_idx]
            train_y = column[train_idx]
            test_y = column[test_idx]
            
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
                results['thresholds_used'].append(threshold_used)
                test_scores = test_pred_raw  # ROC用连续分数
            else:
                train_y_pred = current_model.predict(train_X)
                test_y_pred = current_model.predict(test_X)
                threshold_used = None
                
                # 获取连续分数用于ROC
                if hasattr(current_model, 'predict_proba'):
                    test_scores = current_model.predict_proba(test_X)[:, 1]
                elif hasattr(current_model, 'decision_function'):
                    test_scores = current_model.decision_function(test_X)
                else:
                    test_scores = test_y_pred.astype(float)  # 回退

            # 性能评估 - 使用连续分数
            fpr, tpr, thresholds = roc_curve(test_y, test_scores)
            auc_score = auc(fpr, tpr)
            
            train_acc = balanced_accuracy_score(train_y, train_y_pred)
            test_acc = balanced_accuracy_score(test_y, test_y_pred)
            
            # 混淆矩阵和F分数
            cm = confusion_matrix(test_y, test_y_pred).flatten()
            fscore_dict = classification_report(test_y, test_y_pred, labels=[0, 1], output_dict=True)
            
            f_scores = [
                fscore_dict["weighted avg"]["precision"],
                fscore_dict["weighted avg"]["recall"],
                fscore_dict["weighted avg"]["f1-score"],
                0  # 预留位置
            ]
            
            # 收集结果
            results['train_accuracy'].append(train_acc)
            results['test_accuracy'].append(test_acc)
            results['trained_models'].append(current_model)
            results['fpr_values'].append(fpr)
            results['tpr_values'].append(tpr)
            results['thresholds_list'].append(thresholds)
            results['auc_list'].append(auc_score)
            results['f_scores'].append(f_scores)
            results['confusion_matrices'].append(cm)
            
            # 更新最佳模型
            if test_acc > self.best_score:
                self.best_score = test_acc
                self.best_model = current_model
                log_message(f"发现更高分数：{self.best_score:.4f} (第{fold_idx}折)")
            
            # 更新进度
            if progress_callback:
                progress = fold_idx / total_folds
                progress_callback(progress, f'交叉验证进度: {fold_idx}/{total_folds} ({progress:.1%})')
        
        log_message(f"交叉验证完成！最优模型分数：{self.best_score:.4f}")
        
        # 转换列表为数组（保持与原代码兼容）
        results['f_scores'] = np.array(results['f_scores'])
        results['confusion_matrices'] = np.array(results['confusion_matrices'])
        
        # 保存训练结果
        self.save_training_results(results)
        
        self.training_results = results
        return results

    def save_training_results(self, results):
        """保存训练结果到文件"""
        log_message(f"交叉验证统计:")
        log_message(f"  - 平均测试精度: {np.mean(results['test_accuracy']):.4f}")
        log_message(f"  - 标准差: {np.std(results['test_accuracy']):.4f}")
        log_message(f"  - 95%置信区间: [{np.percentile(results['test_accuracy'], 2.5):.4f}, {np.percentile(results['test_accuracy'], 97.5):.4f}]")
        log_message("保存训练结果文件...")
        
        try:
            from datetime import datetime
            from config import output_manager

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            model_type = type(self.best_model).__name__ if self.best_model else "Unknown"
            run_stem = f"{model_type}_{timestamp}"

            # 保存最佳模型
            if self.best_model is not None:
                filename = f"{run_stem}.joblib"
                model_path = output_manager.get_path('model', filename)

                # 提取训练特征列表（m/z 值）
                _, _, df = data_store.get_training_data()
                training_features = []
                if df is not None:
                    for name in df.index.tolist()[1:]:  # 跳过 'class' 行
                        try:
                            training_features.append(float(name))
                        except ValueError:
                            pass

                # 从训练数据文件名推断归一化方法
                training_data_path = data_store.get_training_data_path() or ''
                basename = os.path.basename(training_data_path)
                if '_max' in basename:
                    norm_method = 'max'
                elif '_sum' in basename:
                    norm_method = 'sum'
                elif '_median' in basename:
                    norm_method = 'median'
                else:
                    norm_method = None

                # 打包保存：模型 + 特征元数据 + PLS阈值（如有）
                model_bundle = {
                    "model": self.best_model,
                    "training_features": training_features,
                    "normalization_method": norm_method,
                }
                if len(results['thresholds_used']) > 0:
                    mean_threshold = np.mean(results['thresholds_used'])
                    model_bundle["pls_threshold"] = mean_threshold
                    log_message(f"PLS回归平均最优阈值: {mean_threshold:.4f}")

                dump(model_bundle, model_path)
                data_store.set_latest_trained_model(self.best_model, model_path)
                log_message(f"模型已保存: {filename}（含 {len(training_features)} 个特征，归一化={norm_method}）")
                log_message(f"测试集分数: {self.best_score:.4f}")

            # 所有指标合并保存为单个 json，与模型文件同名
            import json, math

            def _to_native(obj):
                """递归将 numpy 类型转为 Python 原生类型，inf/nan 替换为 None"""
                if isinstance(obj, np.ndarray):
                    return _to_native(obj.tolist())
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    v = float(obj)
                    return None if math.isinf(v) or math.isnan(v) else v
                if isinstance(obj, float):
                    return None if math.isinf(obj) or math.isnan(obj) else obj
                if isinstance(obj, list):
                    return [_to_native(x) for x in obj]
                if isinstance(obj, dict):
                    return {k: _to_native(v) for k, v in obj.items()}
                return obj

            def _write_metrics(data, f, indent=0):
                """dict 每个 key 独占一行，数组值紧凑内联"""
                pad = '  ' * indent
                f.write('{\n')
                items = list(data.items())
                for i, (k, v) in enumerate(items):
                    sep = ',' if i < len(items) - 1 else ''
                    f.write(f'{pad}  {json.dumps(k, ensure_ascii=False)}: ')
                    if isinstance(v, dict):
                        _write_metrics(v, f, indent + 1)
                    else:
                        f.write(json.dumps(v, ensure_ascii=False, separators=(',', ':')))
                    f.write(sep + '\n')
                f.write(pad + '}')

            # 获取数据集元数据
            row, column, _ = data_store.get_training_data()
            from data_store import class_manager
            class_names = list(class_manager.names) if class_manager.names else []

            # confusion_matrix flatten 顺序：[TN, FP, FN, TP]
            cm_dicts = [
                {"tn": int(cm[0]), "fp": int(cm[1]), "fn": int(cm[2]), "tp": int(cm[3])}
                for cm in results['confusion_matrices']
            ]
            # f_scores 原结构 [precision, recall, f1, 0(占位)]，去掉占位符
            fs_dicts = [
                {"precision": fs[0], "recall": fs[1], "f1": fs[2]}
                for fs in results['f_scores']
            ]

            metrics_path = output_manager.get_path('metrics', f"{run_stem}.json")
            metrics_data = _to_native({
                "meta": {
                    "model": model_type,
                    "timestamp": timestamp,
                    "cv": f"{CV_SPLITS}折×{CV_REPEATS}次重复 ({len(results['test_accuracy'])}次迭代)",
                    "n_samples": int(len(column)),
                    "class_names": class_names,
                    "threshold_strategy": "Youden's J" if results['thresholds_used'] else "model default",
                },
                "confusion_matrices": cm_dicts,
                "f_scores": fs_dicts,
                "auc_list": results['auc_list'],
                "roc_curve": {
                    "fpr": results['fpr_values'],
                    "tpr": results['tpr_values'],
                    "thresholds": results['thresholds_list'],
                },
                "thresholds_used": results['thresholds_used'],
            })
            with open(metrics_path, 'w', encoding='utf-8') as f:
                _write_metrics(metrics_data, f)
            log_message(f"指标已保存: {run_stem}.json")

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
            "mean_train_accuracy": np.mean(results['train_accuracy']),
            "mean_test_accuracy": np.mean(results['test_accuracy']),
            "mean_auc": np.mean(results['auc_list']),
            "n_iterations": len(results['test_accuracy']),
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
                results['train_accuracy'],
                results['test_accuracy'],
                results['f_scores'],
                results['confusion_matrices'],
                results['fpr_values'],
                results['tpr_values'],
                results['auc_list'],
                thresholds,
                root
            )
            

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