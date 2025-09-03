# output_manager.py - 简单的输出文件管理

# 标准库导入
import os
import subprocess
import sys
from pathlib import Path

# 第三方库导入
import joblib
import numpy as np

# 本地模块导入
from utils import log_message


class OutputManager:
    """简单的输出文件管理器 - 按类型分类保存文件"""

    def __init__(self, base_dir="../outputs"):
        script_dir = Path(__file__).parent.absolute()
        self.base_dir = script_dir / base_dir
        self.create_directories()

    def create_directories(self):
        """创建4个基本的输出目录"""
        directories = ['data', 'models', 'results', 'charts']

        for dir_name in directories:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        log_message(f"输出目录已创建: {self.base_dir.absolute()}")

    def get_path(self, category, filename=None):
        """
        获取指定类别的文件保存路径

        参数:
            category: 文件类别 ('data', 'models', 'results', 'charts')
            filename: 文件名

        返回:
            Path: 完整的文件路径
        """
        category_map = {
            'data': 'data',
            'model': 'models',
            'result': 'results',
            'chart': 'charts'
        }

        folder = category_map.get(category, 'results')  # 默认放在results
        directory_path = self.base_dir / folder

         # 确保目录存在
        directory_path.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            return str(directory_path.absolute())  # 返回目录路径
        else:
            return directory_path / filename  # 返回文件路径

    def save_file(self, content, category, filename, save_method='default'):
        """
        保存文件到指定类别目录

        参数:
            content: 要保存的内容
            category: 文件类别
            filename: 文件名
            save_method: 保存方法 ('pandas', 'joblib', 'numpy', 'matplotlib', 'default')
        """
        file_path = self.get_path(category, filename)

        try:
            if save_method == 'pandas':
                content.to_csv(file_path, index=True, float_format='%.8f')
            elif save_method == 'joblib':
                joblib.dump(content, file_path)
            elif save_method == 'numpy':
                np.savetxt(file_path, content, delimiter=",")
            elif save_method == 'numpy_save':
                np.save(file_path, content)
            elif save_method == 'matplotlib':
                content.savefig(file_path, dpi=100, bbox_inches='tight')
            else:
                # 默认方法，适用于简单文本
                with open(file_path, 'w') as f:
                    f.write(str(content))

            log_message(f"文件已保存: {file_path}")
            return str(file_path)

        except Exception as e:
            log_message(f"保存文件失败 {filename}: {str(e)}", "ERROR")
            return None

    def get_results_summary(self):
        """获取结果文件夹的内容摘要"""
        summary = {}

        for category in ['data', 'models', 'results', 'charts']:
            category_dir = self.base_dir / category
            if category_dir.exists():
                files = list(category_dir.glob('*'))
                summary[category] = {
                    'count': len(files),
                    'files': [f.name for f in files if f.is_file()]
                }
            else:
                summary[category] = {'count': 0, 'files': []}

        return summary

    def open_output_folder(self):
        """打开输出文件夹（跨平台）"""

        try:
            if sys.platform == "win32":
                os.startfile(self.base_dir)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", self.base_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.base_dir])

            log_message(f"已打开输出文件夹: {self.base_dir}")

        except Exception as e:
            log_message(f"无法打开文件夹: {str(e)}", "WARNING")


# 全局实例
output_manager = OutputManager()
