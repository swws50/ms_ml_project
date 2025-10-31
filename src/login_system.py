# login_system.py - 极简登录界面

import customtkinter as ctk
from pathlib import Path
import sys

from utils import set_window_icon
from config import ICON_CONFIG 


class SimpleLogin:
    """极简登录界面 - 任意输入都可通过"""
    
    def __init__(self):
        ctk.set_appearance_mode("light")
        self.root = ctk.CTk()
        self.setup_window()
        self.create_interface()

    def setup_window(self):
        """设置窗口"""
        self.root.title("用户登录")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(fg_color='white') 
        set_window_icon(self.root)
        self.root.after(10, self.center_window)
        
    def center_window(self):
        """窗口居中显示"""
        try:
            # 计算居中位置
            window_width, window_height = 450, 550
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            
            self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        except:
            pass  # 静默错误

    def create_interface(self):
        """创建界面"""
        try:
            # 主框架
            main_frame = ctk.CTkFrame(self.root, fg_color="white")
            main_frame.pack(expand=True, fill="both", padx=15, pady=15)
            
            # 标题
            title_label = ctk.CTkLabel(main_frame, text="用户登录", font=("Microsoft YaHei", 20, "bold"))
            title_label.pack(pady=8)
            
            # 显示图片
            self.show_image(main_frame)
            
            # 应用说明
            title_label = ctk.CTkLabel(main_frame, text="基于质谱指纹图谱的肝癌早筛系统", font=("Microsoft YaHei", 20, "bold"))
            title_label.pack(pady=12)

            # 用户名
            self.username_entry = ctk.CTkEntry(main_frame, placeholder_text="用户名", height=32)
            self.username_entry.pack(pady=8, fill="x", padx=8)
            
            # 密码
            self.password_entry = ctk.CTkEntry(main_frame, placeholder_text="密码", show="*", height=32)
            self.password_entry.pack(pady=8, fill="x", padx=8)
            
            # 登录按钮
            login_btn = ctk.CTkButton(main_frame, text="登录", command=self.login, height=32)
            login_btn.pack(pady=15, fill="x", padx=8)
            
            # 回车登录
            self.username_entry.bind("<Return>", lambda e: self.login())
            self.password_entry.bind("<Return>", lambda e: self.login())
            
        except:
            pass  # 静默错误
        
    def show_image(self, parent):
        """显示图片 - 使用 config.py 的配置"""
        try:
            from config import ICON_CONFIG
            
            # 从配置中获取图片路径（已经是正确的绝对路径）
            image_path = ICON_CONFIG.get('app_icon_png')
            
            if image_path and Path(image_path).exists():
                from PIL import Image
                image = ctk.CTkImage(
                    light_image=Image.open(image_path),
                    dark_image=Image.open(image_path),
                    size=(250, 250)
                )
                image_label = ctk.CTkLabel(parent, image=image, text="")
                image_label.pack(pady=8)
                # 保持引用防止被垃圾回收
                parent._image_ref = image
            else:
                # 图片不存在，显示占位文本
                placeholder = ctk.CTkLabel(parent, text="[应用图标]", text_color="gray")
                placeholder.pack(pady=15)
        except Exception as e:
            # 如果出错，显示占位符
            try:
                placeholder = ctk.CTkLabel(parent, text="[应用图标]", text_color="gray")
                placeholder.pack(pady=15)
            except:
                pass

        
    def login(self):
        """直接登录，无需验证"""
        try:
            self.root.destroy()
            # 启动主程序
            from main import MainGUIManager, ctk
            
            root = ctk.CTk()
            app = MainGUIManager(root)
            root.mainloop()
        except:
            # 如果启动失败，直接退出
            try:
                self.root.quit()
            except:
                pass
        
    def run(self):
        """运行"""
        try:
            self.root.mainloop()
        except:
            pass

if __name__ == "__main__":
    login = SimpleLogin()
    login.run()