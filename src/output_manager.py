# output_manager.py - 支持项目管理的输出文件管理

# 标准库导入
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# 第三方库导入
import joblib
import numpy as np

# 本地模块导入
from utils import log_message


class OutputManager:
    """支持项目管理的输出文件管理器"""

    def __init__(self, base_dir="../outputs"):
        script_dir = Path(__file__).parent.absolute()
        self.base_dir = script_dir / base_dir
        self.config_file = self.base_dir / "project_config.json"
        self.current_project = None
        
        self._ensure_base_structure()
        self._load_project_config()

    def _ensure_base_structure(self):
        """确保基础目录结构存在"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果没有配置文件，创建默认项目
        if not self.config_file.exists():
            self._create_default_project()

    def _create_default_project(self):
        """创建默认项目"""
        default_config = {
            "current_project": "默认项目",
            "projects": {
                "默认项目": {
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "description": "系统默认项目"
                }
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        # 创建默认项目的目录结构
        self._create_project_directories("默认项目")

    def _load_project_config(self):
        """加载项目配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.current_project = config.get("current_project", "默认项目")
                self.projects = config.get("projects", {})
                log_message(f"已加载项目配置，当前项目: {self.current_project}")
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_default_project()
            self._load_project_config()

    def _save_project_config(self):
        """保存项目配置"""
        config = {
            "current_project": self.current_project,
            "projects": self.projects
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _create_project_directories(self, project_name):
        """为项目创建4个基本的输出目录"""
        directories = ['data', 'models', 'results', 'charts']
        project_path = self.base_dir / project_name
        
        for dir_name in directories:
            dir_path = project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        log_message(f"项目目录已创建: {project_path.absolute()}")

    def create_directories(self):
        """创建当前项目的基本输出目录（保持向后兼容）"""
        if self.current_project:
            self._create_project_directories(self.current_project)
        else:
            log_message("错误：没有设置当前项目", "ERROR")

    def get_path(self, category, filename=None):
        """
        获取指定类别的文件保存路径（基于当前项目）

        参数:
            category: 文件类别 ('data', 'models', 'results', 'charts')
            filename: 文件名

        返回:
            Path: 完整的文件路径
        """
        if not self.current_project:
            log_message("警告：没有设置当前项目，使用默认项目", "WARNING")
            self.current_project = "默认项目"

        category_map = {
            'data': 'data',
            'model': 'models',
            'result': 'results',
            'chart': 'charts'
        }

        folder = category_map.get(category, 'results')  # 默认放在results
        directory_path = self.base_dir / self.current_project / folder

        # 确保目录存在
        directory_path.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            return str(directory_path.absolute())  # 返回目录路径
        else:
            return directory_path / filename  # 返回文件路径

    def save_file(self, content, category, filename, save_method='default'):
        """
        保存文件到当前项目的指定类别目录

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
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))

            log_message(f"文件已保存到项目 [{self.current_project}]: {file_path}")
            return str(file_path)

        except Exception as e:
            log_message(f"保存文件失败 {filename}: {str(e)}", "ERROR")
            return None

    def get_results_summary(self):
        """获取当前项目的结果文件夹内容摘要"""
        summary = {"current_project": self.current_project}

        for category in ['data', 'models', 'results', 'charts']:
            category_dir = self.base_dir / self.current_project / category
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
        """打开当前项目的输出文件夹（跨平台）"""
        project_path = self.base_dir / self.current_project

        try:
            if sys.platform == "win32":
                os.startfile(project_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", project_path])
            else:  # Linux
                subprocess.run(["xdg-open", project_path])

            log_message(f"已打开项目文件夹 [{self.current_project}]: {project_path}")

        except Exception as e:
            log_message(f"无法打开文件夹: {str(e)}", "WARNING")

    # ===== 项目管理功能 =====

    def get_current_project(self):
        """获取当前项目名称"""
        return self.current_project

    def get_all_projects(self):
        """获取所有项目列表"""
        return list(self.projects.keys())

    def create_project(self, project_name, description=""):
        """
        创建新项目
        
        参数:
            project_name: 项目名称
            description: 项目描述
        
        返回:
            bool: 是否创建成功
        """
        if project_name in self.projects:
            log_message(f"项目 '{project_name}' 已存在", "WARNING")
            return False
        
        # 添加到项目列表
        self.projects[project_name] = {
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description
        }
        
        # 创建项目目录
        self._create_project_directories(project_name)
        
        # 保存配置
        self._save_project_config()
        
        log_message(f"项目 '{project_name}' 创建成功", "SUCCESS")
        return True

    def switch_project(self, project_name):
        """
        切换到指定项目
        
        参数:
            project_name: 项目名称
        
        返回:
            bool: 是否切换成功
        """
        if project_name not in self.projects:
            log_message(f"项目 '{project_name}' 不存在", "ERROR")
            return False
        
        old_project = self.current_project
        self.current_project = project_name
        self._save_project_config()
        
        log_message(f"已从项目 '{old_project}' 切换到 '{project_name}'", "SUCCESS")
        return True

    def delete_project(self, project_name, delete_files=False):
        """
        删除项目
        
        参数:
            project_name: 项目名称
            delete_files: 是否同时删除文件
        
        返回:
            bool: 是否删除成功
        """
        if project_name not in self.projects:
            log_message(f"项目 '{project_name}' 不存在", "WARNING")
            return False
        
        if project_name == self.current_project:
            # 如果删除的是当前项目，切换到其他项目
            remaining_projects = [p for p in self.projects.keys() if p != project_name]
            if remaining_projects:
                self.current_project = remaining_projects[0]
                log_message(f"当前项目被删除，已自动切换到 '{self.current_project}'", "INFO")
            else:
                # 如果没有其他项目，创建默认项目
                self._create_default_project()
                self._load_project_config()
                log_message("创建了新的默认项目", "INFO")
        
        # 从项目列表中移除
        del self.projects[project_name]
        
        # 删除文件（可选）
        if delete_files:
            project_path = self.base_dir / project_name
            if project_path.exists():
                import shutil
                try:
                    shutil.rmtree(project_path)
                    log_message(f"项目文件夹 '{project_name}' 已删除", "INFO")
                except Exception as e:
                    log_message(f"删除项目文件夹失败: {str(e)}", "ERROR")
        
        # 保存配置
        self._save_project_config()
        
        log_message(f"项目 '{project_name}' 删除成功", "SUCCESS")
        return True

    def get_project_info(self, project_name=None):
        """
        获取项目信息
        
        参数:
            project_name: 项目名称，默认为当前项目
        
        返回:
            dict: 项目信息
        """
        if project_name is None:
            project_name = self.current_project
        
        if project_name not in self.projects:
            return None
        
        info = self.projects[project_name].copy()
        info['name'] = project_name
        info['is_current'] = (project_name == self.current_project)
        
        # 统计文件数量
        project_path = self.base_dir / project_name
        if project_path.exists():
            info['file_counts'] = {}
            for category in ['data', 'models', 'results', 'charts']:
                category_path = project_path / category
                if category_path.exists():
                    info['file_counts'][category] = len(list(category_path.glob('*')))
                else:
                    info['file_counts'][category] = 0
        
        return info


# 全局实例
output_manager = OutputManager()

