# model_info.py - 模型信息显示模块

# ========== 标准库导入 ==========
import os

# ========== 第三方库导入 ==========
import customtkinter as ctk
from joblib import load
from sklearn.cross_decomposition import PLSRegression
from tkinter import messagebox

# ========== 本地模块导入 ==========
from config import OUTPUT_FILES
import data_store
from utils import log_message


class ModelInfoDisplay:
    """模型信息显示器类"""
    
    def __init__(self):
        self.model = None
        self.info_window = None
    
    def load_model(self):
        """加载模型"""
        try:
            # 优先从data_store获取
            self.model = data_store.get_best_model()
            
            if self.model is None:
                # 从文件加载
                model_path = OUTPUT_FILES['best_model']
                if not os.path.exists(model_path):
                    return False, "未找到模型文件"
                
                self.model = load(model_path)
                log_message(f"从文件加载模型: {model_path}", "INFO")
            else:
                log_message("从数据存储模块获取模型", "INFO")
            
            return True, "模型加载成功"
            
        except Exception as e:
            error_msg = f"加载模型失败: {str(e)}"
            log_message(error_msg, "ERROR")
            return False, error_msg
    
    def get_model_info(self):
        """
        获取模型详细信息
        
        返回:
            dict: 模型信息字典
        """
        if self.model is None:
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
    
    def show_info_window(self, parent=None):
        """
        显示模型信息窗口
        
        参数:
            parent: 父窗口
        """
        # 检查是否已有窗口打开
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.lift()
            self.info_window.focus_force()
            return
        
        # 加载模型
        success, message = self.load_model()
        if not success:
            messagebox.showerror("错误", message)
            return
        
        # 获取模型信息
        info = self.get_model_info()
        
        # 创建窗口
        self.info_window = ctk.CTkToplevel(parent)
        self.info_window.title(f"模型信息: {info['model_type']}")
        self.info_window.geometry("600x400")
        
        # 窗口置顶设置
        self._setup_window_properties()
        
        # 创建文本框显示信息
        info_text = ctk.CTkTextbox(self.info_window, width=580, height=360)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 插入格式化的信息
        formatted_text = self.format_info_text(info)
        info_text.insert("end", formatted_text)
        
        log_message("模型信息窗口已打开", "INFO")
    
    def _setup_window_properties(self):
        """设置窗口属性"""
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


# ========== 便捷函数接口（保持向后兼容）==========
def show_model_info(parent=None):
    """
    便捷的模型信息显示函数 - 保持与原代码的兼容性
    
    参数:
        parent: 父窗口
    """
    display = ModelInfoDisplay()
    display.show_info_window(parent)


def get_model_summary():
    """
    获取模型摘要信息
    
    返回:
        dict: 模型摘要信息
    """
    display = ModelInfoDisplay()
    success, message = display.load_model()
    
    if not success:
        return {"error": message}
    
    info = display.get_model_info()
    
    # 返回简化的摘要信息
    summary = {
        "model_type": info["model_type"],
        "n_parameters": len(info["parameters"]),
        "has_feature_importance": "feature_importances" in info.get("special_info", {}),
        "has_coefficients": "coefficients" in info.get("special_info", {}),
        "is_pls": "n_components" in info.get("special_info", {})
    }
    
    return summary


# ========== 使用示例 ==========
if __name__ == "__main__":
    # 示例1: 显示模型信息窗口
    # show_model_info()
    
    # 示例2: 获取模型摘要
    summary = get_model_summary()
    print(f"模型摘要: {summary}")
    
    # 示例3: 直接使用类
    display = ModelInfoDisplay()
    success, msg = display.load_model()
    if success:
        info = display.get_model_info()
        formatted_text = display.format_info_text(info)
        print(formatted_text)