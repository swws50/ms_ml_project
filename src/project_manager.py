# project_manager.py - 项目管理独立模块

import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from datetime import datetime
from utils import set_window_icon, log_message

class ProjectManager:
    """项目管理器 - 独立模块"""
    
    def __init__(self):
        self.current_project = None
        self.projects_cache = {}
        self._load_projects()
    
    def _load_projects(self):
        """加载项目列表"""
        try:
            from output_manager import output_manager
            self.projects_cache = {}
            all_projects = output_manager.get_all_projects()
            for project in all_projects:
                self.projects_cache[project] = output_manager.get_project_info(project)
            self.current_project = output_manager.get_current_project()
        except Exception as e:
            log_message(f"加载项目失败: {e}", "ERROR")
    
    def show_manager_dialog(self, parent):
        """显示项目管理主对话框"""
        dialog = ProjectManagerDialog(parent, self)
        return dialog
    
    def create_project_wizard(self, parent):
        """项目创建向导 - 简化流程"""
        wizard = ProjectCreationWizard(parent, self)
        return wizard
    
    def get_current_project(self):
        return self.current_project
    
    def get_all_projects(self):
        return list(self.projects_cache.keys())
    
    def get_project_info(self, project_name):
        return self.projects_cache.get(project_name)
    
    def refresh_projects(self):
        """刷新项目列表"""
        self._load_projects()
    
    def switch_project(self, project_name):
        """切换项目"""
        try:
            from output_manager import output_manager
            if output_manager.switch_project(project_name):
                self.current_project = project_name
                log_message(f"已切换到项目: {project_name}", "SUCCESS")
                return True
            return False
        except Exception as e:
            log_message(f"切换项目失败: {e}", "ERROR")
            return False
    
    def create_project(self, name, description="", template="通用项目"):
        """创建项目"""
        try:
            from output_manager import output_manager
            if output_manager.create_project(name, description):
                self._apply_template(name, template)
                self.refresh_projects()
                log_message(f"项目 '{name}' 创建成功", "SUCCESS")
                return True
            return False
        except Exception as e:
            log_message(f"创建项目失败: {e}", "ERROR")
            return False
    
    def delete_project(self, project_name, delete_files=False):
        """删除项目"""
        try:
            from output_manager import output_manager
            if output_manager.delete_project(project_name, delete_files):
                self.refresh_projects()
                action = "及文件" if delete_files else "配置"
                log_message(f"项目 '{project_name}' 的{action}已删除", "SUCCESS")
                return True
            return False
        except Exception as e:
            log_message(f"删除项目失败: {e}", "ERROR")
            return False
    
    def _apply_template(self, project_name, template):
        """应用项目模板"""
        # 这里可以根据不同模板创建不同的初始文件结构
        templates = {
            "强度预测": {
                "description": "混凝土强度预测项目",
                "default_model": "RandomForestRegressor"
            },
            "质量分析": {
                "description": "产品质量分析项目", 
                "default_model": "PLSRegression"
            },
            "回归分析": {
                "description": "回归分析项目",
                "default_model": "LinearRegression"
            }
        }
        
        if template in templates:
            # 可以在这里创建模板特定的配置文件等
            template_info = templates[template]
            log_message(f"应用模板: {template}", "INFO")


class ProjectCreationWizard:
    """简化的项目创建向导"""
    
    def __init__(self, parent, project_manager):
        self.parent = parent
        self.project_manager = project_manager
        self.result = None
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("创建新项目")
        self.dialog.geometry("450x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        set_window_icon(self.dialog)
        
        self._setup_ui()
        self._center_dialog()
    
    def _setup_ui(self):
        """设置UI - 单页面完成所有输入"""
        # 主容器
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(main_frame, text="创建新项目", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(0, 20))
        
        # 项目名称
        name_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(name_frame, text="项目名称 *:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="请输入项目名称")
        self.name_entry.pack(fill="x", pady=(5, 0))
        self.name_entry.focus()
        
        # 项目描述
        desc_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        desc_frame.pack(fill="x", pady=(15, 5))
        
        ctk.CTkLabel(desc_frame, text="项目描述:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.desc_entry = ctk.CTkTextbox(desc_frame, height=80)
        self.desc_entry.pack(fill="x", pady=(5, 0))
        self.desc_entry.insert("1.0", "请输入项目描述（可选）")
        
        # 项目类型选择
        template_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        template_frame.pack(fill="x", pady=(15, 5))
        
        ctk.CTkLabel(template_frame, text="项目类型:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.template_var = ctk.StringVar(value="通用项目")
        template_menu = ctk.CTkOptionMenu(
            template_frame, 
            values=["通用项目", "强度预测", "质量分析", "回归分析"],
            variable=self.template_var
        )
        template_menu.pack(fill="x", pady=(5, 0))
        
        # 选项设置
        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(15, 5))
        
        ctk.CTkLabel(options_frame, text="选项:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.auto_switch_var = ctk.BooleanVar(value=True)
        auto_switch_cb = ctk.CTkCheckBox(
            options_frame, 
            text="创建后自动切换到此项目",
            variable=self.auto_switch_var
        )
        auto_switch_cb.pack(anchor="w", pady=(5, 0))
        
        # 提示信息
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(15, 5))
        
        info_text = "提示：项目名称将用作文件夹名称，建议使用英文或数字"
        info_label = ctk.CTkLabel(info_frame, text=info_text, 
                                 font=ctk.CTkFont(size=10),
                                 text_color="gray")
        info_label.pack(anchor="w")
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(button_frame, text="创建项目", 
                     command=self._create_project,
                     font=ctk.CTkFont(weight="bold")).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="取消", 
                     command=self._cancel).pack(side="right")
        
        # 绑定回车键
        self.dialog.bind('<Return>', lambda e: self._create_project())
    
    def _create_project(self):
        """创建项目"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "项目名称不能为空")
            self.name_entry.focus()
            return
        
        # 验证项目名称格式
        if not self._validate_project_name(name):
            messagebox.showerror("错误", "项目名称只能包含字母、数字、下划线和短横线")
            self.name_entry.focus()
            return
        
        desc = self.desc_entry.get("1.0", "end-1c").strip()
        if desc == "请输入项目描述（可选）":
            desc = ""
        
        template = self.template_var.get()
        auto_switch = self.auto_switch_var.get()
        
        # 创建项目
        if self.project_manager.create_project(name, desc, template):
            self.result = {
                "name": name, 
                "description": desc, 
                "template": template,
                "auto_switch": auto_switch
            }
            
            # 自动切换项目
            if auto_switch:
                if self.project_manager.switch_project(name):
                    messagebox.showinfo("成功", f"项目 '{name}' 创建成功并已切换！")
                else:
                    messagebox.showinfo("成功", f"项目 '{name}' 创建成功！\n但切换失败，请手动切换。")
            else:
                messagebox.showinfo("成功", f"项目 '{name}' 创建成功！")
            
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", f"项目 '{name}' 已存在或创建失败")
    
    def _validate_project_name(self, name):
        """验证项目名称格式"""
        import re
        # 只允许字母、数字、下划线和短横线
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, name) is not None
    
    def _cancel(self):
        """取消创建"""
        self.result = None
        self.dialog.destroy()
    
    def _center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"450x600+{x}+{y}")


class ProjectManagerDialog:
    """改进的项目管理对话框"""
    
    def __init__(self, parent, project_manager):
        self.parent = parent
        self.project_manager = project_manager
        
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("项目管理")
        self.dialog.geometry("700x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        set_window_icon(self.dialog)
        
        self._setup_ui()
        self._center_dialog()
        self._refresh_display()
    
    def _setup_ui(self):
        """设置UI - 使用更现代的布局"""
        # 顶部工具栏
        toolbar = ctk.CTkFrame(self.dialog, height=60)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))
        toolbar.pack_propagate(False)
        
        # 左侧按钮组
        left_buttons = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_buttons.pack(side="left", fill="y", padx=5, pady=5)
        
        ctk.CTkButton(left_buttons, text="+ 新建项目", 
                     command=self._quick_create,
                     font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkButton(left_buttons, text="刷新", 
                     command=self._refresh_display).pack(side="left", padx=5)
        
        # 右侧状态显示
        right_info = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_info.pack(side="right", fill="y", padx=5, pady=5)
        
        current_frame = ctk.CTkFrame(right_info, fg_color="transparent")
        current_frame.pack(side="right")
        
        ctk.CTkLabel(current_frame, text="当前项目:", 
                    font=ctk.CTkFont(size=12)).pack(side="top", anchor="e")
        self.current_label = ctk.CTkLabel(current_frame, text="", 
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color="blue")
        self.current_label.pack(side="top", anchor="e")
        
        # 项目列表区域
        list_frame = ctk.CTkFrame(self.dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 列表标题
        title_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(title_frame, text="项目列表", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # 项目表格容器
        self.table_frame = ctk.CTkScrollableFrame(list_frame)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 底部操作按钮
        bottom_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=5)
        
        # 批量操作按钮
        action_buttons = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_buttons.pack(side="left")
        
        ctk.CTkButton(action_buttons, text="切换项目", 
                     command=self._switch_project).pack(side="left", padx=5)
        ctk.CTkButton(action_buttons, text="删除项目", 
                     command=self._delete_project,
                     fg_color="red", hover_color="darkred").pack(side="left", padx=5)
        
        # 关闭按钮
        ctk.CTkButton(bottom_frame, text="关闭", 
                     command=self.dialog.destroy).pack(side="right", padx=5)
    
    def _create_project_table(self):
        """创建项目表格"""
        # 清空现有内容
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # 配置主表格的列宽度
        self.table_frame.grid_columnconfigure(0, weight=0, minsize=150)
        self.table_frame.grid_columnconfigure(1, weight=0, minsize=120)
        self.table_frame.grid_columnconfigure(2, weight=0, minsize=80)
        self.table_frame.grid_columnconfigure(3, weight=1, minsize=200)
        
        # 创建表头
        headers = ["项目名称", "创建时间", "文件数量", "描述"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(self.table_frame, text=header, 
                            font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # 项目数据行
        self.project_rows = []
        current_project = self.project_manager.get_current_project()
        
        row = 1
        for project_name in self.project_manager.get_all_projects():
            project_info = self.project_manager.get_project_info(project_name)
            
            # 创建行容器框架
            row_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent", corner_radius=5)
            if project_name == current_project:
                row_frame.configure(border_width=2, border_color="blue")
            row_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=2, pady=1)
            
            # 配置行容器的列宽度
            row_frame.grid_columnconfigure(0, weight=0, minsize=140)
            row_frame.grid_columnconfigure(1, weight=0, minsize=110) 
            row_frame.grid_columnconfigure(2, weight=0, minsize=70)
            row_frame.grid_columnconfigure(3, weight=1, minsize=190)
            
            # 在行容器内创建标签
            name_label = ctk.CTkLabel(row_frame, text=project_name,
                                    font=ctk.CTkFont(weight="bold" if project_name == current_project else "normal"),
                                    text_color="blue" if project_name == current_project else "black")
            name_label.grid(row=0, column=0, padx=5, pady=3, sticky="w")
            
            created_date = project_info.get('created_date', '未知') if project_info else '未知'
            date_label = ctk.CTkLabel(row_frame, text=created_date)
            date_label.grid(row=0, column=1, padx=5, pady=3, sticky="w")
            
            file_counts = project_info.get('file_counts', {}) if project_info else {}
            total_files = sum(file_counts.values()) if file_counts else 0
            files_label = ctk.CTkLabel(row_frame, text=str(total_files))
            files_label.grid(row=0, column=2, padx=5, pady=3, sticky="w")
            
            description = project_info.get('description', '无描述') if project_info else '无描述'
            desc_label = ctk.CTkLabel(row_frame, text=description[:30] + "..." if len(description) > 30 else description)
            desc_label.grid(row=0, column=3, padx=5, pady=3, sticky="w")
            
            # 存储行信息
            self.project_rows.append({
                'name': project_name,
                'frame': row_frame,
                'is_current': project_name == current_project
            })
            
            # 绑定点击事件
            self._bind_row_click(row_frame, project_name)
            
            row += 1

    def _bind_row_click(self, row_frame, project_name):
        """绑定行点击事件"""
        def on_click(event):
            self.selected_project = project_name
            # 清除所有边框
            for row_info in self.project_rows:
                if row_info['is_current']:
                    row_info['frame'].configure(border_width=2, border_color="blue")
                else:
                    row_info['frame'].configure(border_width=0)
            # 给选中的行添加橙色边框
            if not any(row['name'] == project_name and row['is_current'] for row in self.project_rows):
                row_frame.configure(border_width=2, border_color="orange")
        
        row_frame.bind("<Button-1>", on_click)
        for child in row_frame.winfo_children():
            child.bind("<Button-1>", on_click)
        
    def _quick_create(self):
        """快速创建项目"""
        wizard = self.project_manager.create_project_wizard(self.dialog)
        self.dialog.wait_window(wizard.dialog)
        
        if wizard.result:
            self._refresh_display()
    
    def _switch_project(self):
        """切换项目"""
        if not hasattr(self, 'selected_project'):
            messagebox.showinfo("提示", "请先选择要切换的项目")
            return
        
        if self.selected_project == self.project_manager.get_current_project():
            return  # 静默处理，不显示提示
        
        if self.project_manager.switch_project(self.selected_project):
            self._refresh_display()  # 直接刷新，不显示成功消息
            # 清除选择状态
            if hasattr(self, 'selected_project'):
                delattr(self, 'selected_project')
    
    def _delete_project(self):
        """删除项目"""
        if not hasattr(self, 'selected_project'):
            messagebox.showinfo("提示", "请先选择要删除的项目")
            return
        
        all_projects = self.project_manager.get_all_projects()
        if len(all_projects) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个项目")
            return
        
        # 确认删除
        response = messagebox.askyesnocancel(
            "确认删除", 
            f"确定要删除项目 '{self.selected_project}' 吗？\n\n"
            "选择:\n"
            "是 - 删除项目配置和所有文件\n"
            "否 - 仅删除项目配置，保留文件\n"
            "取消 - 不删除"
        )
        
        if response is not None:  # 用户没有选择取消
            delete_files = response  # True=删除文件，False=保留文件
            
            if self.project_manager.delete_project(self.selected_project, delete_files):
                action = "及文件" if delete_files else "配置"
                messagebox.showinfo("成功", f"项目 '{self.selected_project}' 的{action}已删除")
                self._refresh_display()
                if hasattr(self, 'selected_project'):
                    delattr(self, 'selected_project')
            else:
                messagebox.showerror("错误", "删除项目失败")
    
    def _refresh_display(self):
        """刷新显示"""
        self.project_manager.refresh_projects()
        current_project = self.project_manager.get_current_project()
        self.current_label.configure(text=current_project)
        self._create_project_table()
        
        # 清除选择状态（因为表格已重建）
        if hasattr(self, 'selected_project'):
            delattr(self, 'selected_project')
        
        self.table_frame.update_idletasks()

    def _center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (550 // 2)
        self.dialog.geometry(f"700x550+{x}+{y}")


# 为了保持向后兼容性，导出主要类
__all__ = ['ProjectManager', 'ProjectCreationWizard', 'ProjectManagerDialog']