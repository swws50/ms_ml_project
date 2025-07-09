# model_training.py - 模型训练和预测模块 (使用data_store版本)

import os
import numpy as np
import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import (balanced_accuracy_score, confusion_matrix, 
                            classification_report, roc_curve, auc)
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import LogisticRegressionCV
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from joblib import dump, load
from tkinter import messagebox, filedialog, scrolledtext
import tkinter

from config import (MODEL_CONFIGS, OUTPUT_FILES, TRAINING_ITERATIONS, TEST_SIZE, 
                   REVERSE_CLASS_MAPPING, DEFAULT_MZ_VALUES)
from utils import log_message, validate_data, clear_log
from data_processing import process_file
from visualization import visualize_performance
import data_store  # 导入数据存储模块

def find_optimal_threshold(y_true, y_pred_proba):
    """
    基于ROC曲线分析寻找最优分类阈值。
    
    参数:
        y_true: 真实类别标签
        y_pred_proba: 模型的连续预测值或概率估计
        
    返回:
        float: 最优分类阈值
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    # 找到最优点（约登指数最大的点）
    optimal_idx = np.argmax(tpr - fpr)
    return thresholds[optimal_idx]

def predict_by_wrapper(progress_label, progress_bar, balanced_accuracy_train_label, 
                      balanced_accuracy_test_label, model_save_status_label, 
                      exact_selection, help_system, root):
    """
    执行机器学习模型的训练、评估和保存的包装函数
    """
    # 从data_store获取训练数据
    if not data_store.has_training_data():
        log_message("错误: 数据未正确加载", "ERROR")
        messagebox.showerror("数据错误", "未找到有效训练数据，请先选择Excel文件。")
        return
    
    row, column, df = data_store.get_training_data()
    log_message(f"从数据存储模块获取训练数据: {row.shape}", "INFO")
    
    # 清空日志旧信息
    clear_log()
    log_message("=> 开始模型训练...")
    
    # 数据验证
    is_valid, message = validate_data(row, column)
    if not is_valid:
        log_message(f"错误: {message}", "ERROR")
        messagebox.showerror("数据验证错误", message)
        progress_bar['value'] = 0
        return

    log_message(f"使用模型: {exact_selection}")
    log_message("数据验证通过，开始训练...")

    # 初始化结果存储
    balanced_accuracy_train = []  
    balanced_accuracy_test = []
    trained_models = []
    fpr_list = []
    tpr_list = []
    thresholds_list = []
    auc_list = []
    Fscores = np.zeros((TRAINING_ITERATIONS, 4))
    thresholds_used = []
    confusion_matrixs = np.zeros((TRAINING_ITERATIONS, 4))
    best_score = -1
    best_model = None

    try:
        # 获取模型类和参数
        model_class = globals()[exact_selection]
        params = MODEL_CONFIGS[exact_selection]

        # 主训练循环
        log_message(f"开始{TRAINING_ITERATIONS}轮训练循环...")
        for i in tqdm.tqdm(range(TRAINING_ITERATIONS)):
            percentage = (i + 1) / TRAINING_ITERATIONS * 100
            progress_label.config(text='分析进度: {0:.2f}%'.format(percentage))
            progress_bar['value'] = percentage
            root.update()

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
                
                optimal_threshold = find_optimal_threshold(train_y, train_pred_raw)
                thresholds_used.append(optimal_threshold)
                
                train_y_pred = (train_pred_raw > optimal_threshold).astype(int)
                test_y_pred = (test_pred_raw > optimal_threshold).astype(int)
            else:
                train_y_pred = current_model.predict(train_X)
                test_y_pred = current_model.predict(test_X)
            
            # 性能评估
            fpr, tpr, thresholds = roc_curve(test_y, test_y_pred)
            fpr_list.append(fpr)
            tpr_list.append(tpr)
            thresholds_list.append(thresholds)
            auc_list.append(auc(fpr, tpr))

            # 准确率计算
            train_acc = balanced_accuracy_score(train_y, train_y_pred)
            test_acc = balanced_accuracy_score(test_y, test_y_pred)
            balanced_accuracy_train.append(train_acc)
            balanced_accuracy_test.append(test_acc)

            # 混淆矩阵和F分数
            confusion_matrixs[i] = confusion_matrix(test_y, test_y_pred).flatten()
            
            fscore_dict = classification_report(test_y, test_y_pred, labels=[0, 1], output_dict=True)
            Fscores[i][0] = fscore_dict["weighted avg"]["precision"]
            Fscores[i][1] = fscore_dict["weighted avg"]["recall"]
            Fscores[i][2] = fscore_dict["weighted avg"]["f1-score"]

            trained_models.append(current_model)

            # 更新最佳模型
            if test_acc > best_score:
                best_score = test_acc
                best_model = current_model
                log_message(f"发现更高分数：{best_score:.4f} (迭代{i+1})")

        log_message(f"训练完成！最优模型分数：{best_score:.4f}")

        # 保存最佳模型到data_store
        data_store.set_best_model(best_model)
        log_message("最佳模型已保存到数据存储模块", "SUCCESS")

        # 保存训练结果
        save_training_results(confusion_matrixs, Fscores, auc_list, fpr_list, 
                             tpr_list, thresholds_list, thresholds_used, best_model, best_score)

        # 更新UI显示
        mean_balanced_accuracy_train = np.mean(balanced_accuracy_train)
        mean_balanced_accuracy_test = np.mean(balanced_accuracy_test)
        balanced_accuracy_train_label.config(text=f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
        balanced_accuracy_test_label.config(text=f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
        
        model_save_status_label.config(text=f'模型保存状态: 已保存 (分数: {best_score:.4f})', fg='green')
        
        log_message(f"平均训练集平衡精度: {mean_balanced_accuracy_train:.4f}")
        log_message(f"平均测试集平衡精度: {mean_balanced_accuracy_test:.4f}")
        log_message("开始生成可视化图表...")
        
        # 推进步骤到"查看结果"
        if help_system:
            help_system.advance_step("view_results")

        # 生成可视化
        if len(trained_models) > 0 and isinstance(trained_models[0], PLSRegression) and len(thresholds_used) > 0:
            visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, 
                                confusion_matrixs, fpr_list, tpr_list, auc_list, thresholds_used, root)
        else:
            visualize_performance(balanced_accuracy_train, balanced_accuracy_test, Fscores, 
                                confusion_matrixs, fpr_list, tpr_list, auc_list, None, root)
            
        log_message("所有任务完成！")

    except Exception as e:
        log_message(f"训练过程中出现错误: {str(e)}", "ERROR")
        messagebox.showerror("训练错误", f"模型训练时出现错误：{str(e)}")
        progress_bar['value'] = 0
        model_save_status_label.config(text='模型保存状态: 训练失败', fg='red')

def save_training_results(confusion_matrixs, Fscores, auc_list, fpr_list, 
                         tpr_list, thresholds_list, thresholds_used, best_model, best_score):
    """保存训练结果到文件"""
    log_message("保存训练结果文件...")
    
    # 保存各种指标
    np.savetxt(OUTPUT_FILES['confusion_matrix'], confusion_matrixs, delimiter=",")
    np.savetxt(OUTPUT_FILES['fscore'], Fscores, delimiter=",")
    np.savetxt(OUTPUT_FILES['auc'], auc_list, delimiter=",")
    np.save(OUTPUT_FILES['fpr_values'], np.array(fpr_list, dtype=object))
    np.save(OUTPUT_FILES['tpr_values'], np.array(tpr_list, dtype=object))
    np.save(OUTPUT_FILES['thresholds_values'], np.array(thresholds_list, dtype=object))
    
    # 保存最佳模型
    if best_model is not None:
        dump(best_model, OUTPUT_FILES['best_model'])
        log_message(f"最优模型已保存到文件，测试集分数: {best_score:.4f}")
    
    # 保存PLS阈值（如果存在）
    if len(thresholds_used) > 0:
        np.savetxt(OUTPUT_FILES['pls_thresholds'], thresholds_used, delimiter=",")
        mean_threshold = np.mean(thresholds_used)
        log_message(f"PLS回归平均最优阈值: {mean_threshold:.4f}")

def get_prediction_probability(model, features):
    """
    获取给定模型对特征的预测概率
    
    参数:
        model: 训练好的模型
        features: 样本特征
        
    返回:
        tuple: (预测类别, 概率数组)
    """
    if isinstance(model, PLSRegression):
        # PLS回归模型处理
        raw_value = model.predict(features).flatten()[0]
        
        try:
            threshold = np.mean(np.loadtxt(OUTPUT_FILES['pls_thresholds'], delimiter=","))
        except:
            threshold = 0.5
            
        prob1 = 1 / (1 + np.exp(-(raw_value - threshold) * 10))
        probs = np.array([1 - prob1, prob1])
        pred = 1 if raw_value > threshold else 0
        
    elif hasattr(model, 'predict_proba'):
        # 有predict_proba方法的模型
        probs = model.predict_proba(features)[0]
        pred = model.predict(features)[0]
        
    elif hasattr(model, 'decision_function'):
        # 有decision_function的模型
        decision_value = model.decision_function(features)
        
        if isinstance(decision_value, np.ndarray):
            decision_value = decision_value.flatten()[0]
            
        prob1 = 1 / (1 + np.exp(-decision_value))
        probs = np.array([1 - prob1, prob1])
        pred = model.predict(features)[0]
        
    else:
        # 其他模型
        pred = model.predict(features)[0]
        probs = np.array([0, 1]) if pred == 1 else np.array([1, 0])
    
    return pred, probs

def predict_unknown_sample(file_path, prediction_result_label, help_system=None):
    """
    预测未知样本的类别
    
    参数:
        file_path: 样本文件路径
        prediction_result_label: 显示结果的标签
        help_system: 帮助系统实例
        
    返回:
        tuple: (预测类别, 概率数组)
    """
    try:
        # 首先尝试从data_store获取模型
        loaded_model = data_store.get_best_model()
        
        # 如果data_store中没有模型，尝试从文件加载
        if loaded_model is None:
            if not os.path.exists(OUTPUT_FILES['best_model']):
                prediction_result_label.config(text="错误，未找到保存的模型文件", fg='red', font=('Helvetica', 12, 'bold'))
                return None, None
            loaded_model = load(OUTPUT_FILES['best_model'])
            log_message("从文件加载模型", "INFO")
        else:
            log_message("从数据存储模块获取模型", "INFO")
        
        # 处理样本数据
        sample_data = process_file(file_path, DEFAULT_MZ_VALUES)
        sample_features = sample_data['Max_Value'].values.reshape(1, -1)

        # 获取预测结果
        prediction, probabilities = get_prediction_probability(loaded_model, sample_features)
        
        # 映射到类别名称
        predicted_class = REVERSE_CLASS_MAPPING.get(prediction, "未知")
        
        # 显示预测结果和概率
        confidence_text = f"类别概率: HC={probabilities[0]:.4f}, LC={probabilities[1]:.4f}"
        result_text = f"预测结果: {predicted_class}\n{confidence_text}"
        result_text += f"\n预测样本: {os.path.basename(file_path)}"
        result_text += f"\n模型信息: {loaded_model.__class__.__name__}"
        
        prediction_result_label.config(text=result_text, 
                                     fg='red' if predicted_class == "LC" else 'green', 
                                     font=('Helvetica', 12, 'bold'))
        
        # 完成"预测样本"步骤
        if help_system:
            help_system.complete_step("predict_sample")

        log_message(f"预测完成 - 样本: {os.path.basename(file_path)}, 结果: {predicted_class}", "SUCCESS")
        return predicted_class, probabilities
        
    except Exception as e:
        error_message = f"预测过程中发生错误：{str(e)}"
        prediction_result_label.config(text=error_message, fg='red', font=('Helvetica', 12, 'bold'))
        log_message(error_message, "ERROR")
        return None, None

def open_file_dialog(prediction_result_label, help_system=None):
    """
    打开文件选择对话框，用于选择要预测的样本文件。
    
    参数:
        prediction_result_label: 用于显示预测结果的标签控件
        help_system: 帮助系统实例
    """
    file_path = filedialog.askopenfilename(
        initialdir="/",
        title="选择要预测的文件",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if file_path:
        predict_unknown_sample(file_path, prediction_result_label, help_system)

def show_model_info():
    """显示加载模型的详细信息窗口"""
    try:
        # 首先尝试从data_store获取模型
        loaded_model = data_store.get_best_model()
        
        # 如果data_store中没有模型，尝试从文件加载
        if loaded_model is None:
            if not os.path.exists(OUTPUT_FILES['best_model']):
                messagebox.showerror("错误", "未找到模型文件")
                return
            loaded_model = load(OUTPUT_FILES['best_model'])
        
        info_window = tkinter.Toplevel()
        info_window.title(f"模型信息: {type(loaded_model).__name__}")
        info_window.geometry("600x400")
        
        # 使用文本框显示模型信息
        info_text = scrolledtext.ScrolledText(info_window, width=70, height=20)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 获取模型信息
        info_text.insert(tkinter.END, f"模型类型: {type(loaded_model).__name__}\n\n")
        
        # 获取模型参数
        info_text.insert(tkinter.END, "模型参数:\n")
        for param_name, param_value in loaded_model.get_params().items():
            info_text.insert(tkinter.END, f"- {param_name}: {param_value}\n")
        
        # 特殊模型信息
        if hasattr(loaded_model, 'feature_importances_'):
            info_text.insert(tkinter.END, "\n特征重要性:\n")
            importances = loaded_model.feature_importances_
            for i, imp in enumerate(importances):
                info_text.insert(tkinter.END, f"- 特征 {i+1}: {imp:.4f}\n")
        
        elif hasattr(loaded_model, 'coef_'):
            info_text.insert(tkinter.END, "\n特征系数:\n")
            coefs = loaded_model.coef_
            if coefs.ndim == 1:
                for i, coef in enumerate(coefs):
                    info_text.insert(tkinter.END, f"- 特征 {i+1}: {coef:.4f}\n")
            
            elif isinstance(loaded_model, PLSRegression):
                info_text.insert(tkinter.END, "\nPLS回归特有信息:\n")
                info_text.insert(tkinter.END, f"- 组件数: {loaded_model.n_components}\n")
                
                if hasattr(loaded_model, 'x_weights_'):
                    info_text.insert(tkinter.END, "\nX权重 (前5个特征的前3个组件):\n")
                    weights = loaded_model.x_weights_
                    for i in range(min(5, weights.shape[0])):
                        weight_str = ", ".join([f"{w:.4f}" for w in weights[i, :min(3, weights.shape[1])]])
                        info_text.insert(tkinter.END, f"- 特征 {i+1}: {weight_str}\n")
                
                if hasattr(loaded_model, 'x_loadings_'):
                    info_text.insert(tkinter.END, "\nX载荷 (前5个特征的前3个组件):\n")
                    loadings = loaded_model.x_loadings_
                    for i in range(min(5, loadings.shape[0])):
                        loading_str = ", ".join([f"{l:.4f}" for l in loadings[i, :min(3, loadings.shape[1])]])
                        info_text.insert(tkinter.END, f"- 特征 {i+1}: {loading_str}\n")
            else:
                for class_idx, class_coef in enumerate(coefs):
                    info_text.insert(tkinter.END, f"\n类别 {class_idx} 的系数:\n")
                    for i, coef in enumerate(class_coef):
                        info_text.insert(tkinter.END, f"- 特征 {i+1}: {coef:.4f}\n")
                        
    except Exception as e:
        messagebox.showerror("错误", f"显示模型信息时出错: {str(e)}")