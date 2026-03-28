# help_system.py - 帮助系统和进度跟踪模块

# 标准库导入
import datetime
import hashlib
import hmac
import json
import os
import platform
import socket
from PIL import Image

# 用于免责声明日志防篡改签名的密钥（打包进 exe 后不可见）
_HMAC_KEY = b"deteqx-saldi-research-2026-\xd7\x9a\x4f\x83"
# 第三方库导入
import customtkinter as ctk

# 本地模块导入
from utils import log_message, set_window_icon, center_window, get_resource_path
from config import ICON_CONFIG 


class HelpSystem:
    """统一的帮助系统类 - 完整功能实现"""

    def __init__(self, root, config_file="../outputs/help_config.json"):
        self.root = root
        self.config_file = config_file
        self.active_tooltips = {}  # 跟踪活动的提示窗口

        self.show_wizard_on_startup = True

        # 为你的程序定制的帮助文本
        self.help_texts = {
            "start_preprocessing": "数据预处理流程\n包括文件分类和智能峰发现\n处理完成后自动生成归一化CSV文件",
            # 数据预处理相关
            "select_files": "智能提峰：自动识别并提取最优特征峰",

            # 训练相关
            "select_excel": "选择已预处理的Excel数据文件\n第一行应为类别标签标签",
            "model_selection": "选择机器学习算法\n• RandomForest: 适合大数据集\n• LogisticRegression: 适合小数据集\n• PLS: 适合高维数据",
            "start_analysis": "开始训练模型\n• 训练时间：约1-3分钟\n• 5折×20次重复交叉验证（共100轮）\n• 若需中途终止，点击菜单栏 ⟲ 重置按钮",

            # 预测相关
            "select_predict_file": "选择要预测的txt格式样本文件\n需要先完成模型训练",
            "model_info": "查看当前训练模型的详细信息\n包括参数、特征重要性等",

            # 状态显示
            "progress": "显示当前任务进度\n训练时会实时更新百分比",
            "results": "显示模型训练结果\n包括准确率、混淆矩阵等指标",
            "log_info": "显示系统运行日志\n记录所有操作和错误信息"
        }

        # 加载用户配置
        self.load_config()

        # UI组件引用
        self.wizard_window = None

    def load_config(self):
        """加载用户配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.show_wizard_on_startup = config.get(
                        'show_wizard_on_startup', True)
        except Exception:
            pass  # 使用默认配置

    def save_config(self):
        """保存用户配置（保留文件中已有的其他字段）"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['show_wizard_on_startup'] = self.show_wizard_on_startup
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  免责声明 — 首次启动弹窗 + 同意日志                                  #
    # ------------------------------------------------------------------ #

    def _get_device_info(self):
        """收集本机设备信息，用于同意日志"""
        info = {
            "hostname": "unknown",
            "local_ip": "unknown",
            "os": "unknown",
            "username": "unknown",
        }
        try:
            info["hostname"] = socket.gethostname()
        except Exception:
            pass
        try:
            # 连接外网地址只是为了探测出口网卡 IP，不实际发送数据
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                info["local_ip"] = socket.gethostbyname(info["hostname"])
            except Exception:
                pass
        try:
            info["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
        except Exception:
            pass
        try:
            info["username"] = os.getlogin()
        except Exception:
            info["username"] = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
        return info

    def _sign_record(self, record: dict) -> str:
        """对记录内容（排除 sig 字段本身）计算 HMAC-SHA256 签名"""
        payload = {k: v for k, v in record.items() if k != "sig"}
        msg = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hmac.new(_HMAC_KEY, msg, hashlib.sha256).hexdigest()

    def _verify_record(self, record: dict) -> bool:
        """验证记录的签名是否完整、未被篡改"""
        sig = record.get("sig", "")
        if not sig:
            return False
        expected = self._sign_record(record)
        return hmac.compare_digest(sig, expected)  # 防时序攻击的常数时间比较

    def _has_valid_agreement(self) -> bool:
        """以配置文件为门控：当前机器是否存在至少一条未被篡改的同意记录"""
        if not os.path.exists(self.config_file):
            return False
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            records = config.get("_ev", [])
            current_hostname = socket.gethostname()
            for record in records:
                if (self._verify_record(record) and
                        record.get("hostname") == current_hostname):
                    return True
        except Exception:
            pass
        return False

    def _log_disclaimer_agreement(self):
        """将同意记录追加写入配置文件的 _ev 字段，并附 HMAC 签名"""
        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "agreed_disclaimer",
            **self._get_device_info(),
        }
        record["sig"] = self._sign_record(record)
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config.setdefault("_ev", []).append(record)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_hover_tip(self, widget, key_or_text, custom_style=None, delay_ms=1000):
        """
        为控件添加悬停提示 - 延迟显示版本

        参数:
            widget: tkinter控件
            key_or_text: 配置键名或直接的提示文本
            custom_style: 自定义样式字典（暂时保留，与CTk兼容）
            delay_ms: 延迟显示时间（毫秒），默认2000ms（2秒）
        """
        # 获取提示文本
        if key_or_text in self.help_texts:
            tip_text = self.help_texts[key_or_text]
        else:
            tip_text = key_or_text

        # 为每个控件创建一个定时器引用
        timer_id = None

        def show_tip_delayed():
            """延迟显示提示"""
            # 先清理所有可能存在的旧提示
            self.hide_all_tips()

            # 检查控件是否还有效
            try:
                x = widget.winfo_rootx() + 20
                y = widget.winfo_rooty() + widget.winfo_height() + 5
            except:
                return  # 控件已被销毁，直接返回

            # 创建提示窗口
            tip_window = ctk.CTkToplevel(widget)
            tip_window.wm_overrideredirect(True)
            tip_window.wm_geometry(f"+{x}+{y}")

            # 设置窗口属性
            tip_window.attributes('-topmost', True)
            tip_window.focus_set = lambda: None  # 禁用焦点获取

            # 创建提示标签
            tip_label = ctk.CTkLabel(tip_window, text=tip_text,
                                     fg_color="#FFFFDD", text_color="black",
                                     font=ctk.CTkFont(size=9), corner_radius=5)
            tip_label.pack(padx=8, pady=5)

            # 保存引用
            self.active_tooltips[widget] = tip_window

            # 添加自动销毁定时器（10秒后自动销毁，防止永久残留）
            tip_window.after(10000, lambda: self.hide_tip(widget))

        def on_enter(event):
            """鼠标进入时启动定时器"""
            nonlocal timer_id
            # 取消之前的定时器（如果存在）
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass

            # 设置延迟定时器
            timer_id = widget.after(delay_ms, show_tip_delayed)

        def on_leave(event):
            """鼠标离开时取消定时器并隐藏提示"""
            nonlocal timer_id
            # 取消定时器
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None

            # 隐藏当前提示
            self.hide_tip(widget)

        def on_click(event):
            """点击时立即取消定时器并隐藏提示"""
            nonlocal timer_id
            # 取消定时器
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None

            # 隐藏提示
            self.hide_tip(widget)

        def on_focus_out(event):
            """失去焦点时隐藏提示"""
            nonlocal timer_id
            if timer_id:
                try:
                    widget.after_cancel(timer_id)
                except:
                    pass
                timer_id = None
            self.hide_tip(widget)

        # 绑定事件
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)      # 左键点击时隐藏
        widget.bind("<FocusOut>", on_focus_out)  # 失去焦点时隐藏

        return self  # 支持链式调用

    def hide_tip(self, widget):
        """隐藏指定控件的提示 - 改进版本"""
        if widget in self.active_tooltips:
            try:
                tip_window = self.active_tooltips[widget]
                if tip_window and tip_window.winfo_exists():
                    tip_window.destroy()
                del self.active_tooltips[widget]
            except Exception:
                # 如果销毁失败，强制从字典中移除
                try:
                    del self.active_tooltips[widget]
                except:
                    pass

                    pass

    def hide_all_tips(self):
        """隐藏所有提示 - 改进版本"""
        # 创建副本以避免在迭代时修改字典
        tips_to_remove = list(self.active_tooltips.keys())
        for widget in tips_to_remove:
            self.hide_tip(widget)

        # 强制清空字典（防止残留）
        self.active_tooltips.clear()

    def show_wizard(self):
        """显示欢迎向导，指导用户使用程序的基本步骤"""
        # 以日志为门控：每次打开向导时验签，防止 config 被手动篡改绕过
        already_agreed = self._has_valid_agreement()

        if self.wizard_window and self.wizard_window.winfo_exists():
            self.wizard_window.lift()
            self.wizard_window.focus_force()
            self.wizard_window.tkraise()
            return

        self.wizard_window = ctk.CTkToplevel(self.root)
        self.wizard_window.title("使用向导")
        center_window(self.wizard_window, 750, 600)
        self.wizard_window.resizable(False, False)
        set_window_icon(self.wizard_window)
        self.wizard_window.attributes('-topmost', True)
        self.wizard_window.focus_force()
        self.wizard_window.lift()
        self.wizard_window.tkraise()
        self.wizard_window.grab_set()
        self.wizard_window.after(1000, lambda: self.wizard_window.attributes('-topmost', False))

        show_again_var = ctk.BooleanVar(value=self.show_wizard_on_startup)

        def _do_close():
            self.show_wizard_on_startup = show_again_var.get()
            self.save_config()
            self.wizard_window.grab_release()
            self.wizard_window.destroy()
            self.wizard_window = None
            self.root.lift()

        def on_closing():
            _do_close()

        def close_wizard():
            _do_close()


        self.wizard_window.protocol("WM_DELETE_WINDOW", on_closing)

        # 创建选项卡视图
        wizard_tabs = ctk.CTkTabview(self.wizard_window, width=680, height=490)
        wizard_tabs.pack(fill='both', expand=True, padx=10, pady=10)

        # 须知 tab
        step0 = wizard_tabs.add("0. 须知")
        ctk.CTkLabel(step0, text="使用前须知",
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 4))
        disclaimer_text = (
            "本软件（DETEQX）仅供学术研究与科学实验使用。请在使用前仔细阅读以下声明：\n\n"
            "1. 本软件不构成医疗器械，不具备任何临床诊断功能。\n\n"
            "2. 本软件的全部输出结果（包括分类概率、评分等数值）均为科学研究参考数据，\n不得作为疾病诊断、临床筛查或任何医疗决策的依据。\n\n"
            "3. 任何与医疗健康相关的决策，请咨询持有执业资质的医疗专业人员。\n\n"
            "4. 开发团队不对因误用本软件输出结果而导致的任何直接或间接后果承担法律责任。\n\n"
            "5. 继续使用本软件，即表示您已充分理解并接受上述全部声明。\n\n"
            "本声明依据《医疗器械监督管理条例》及相关法规制定，适用于所有"
            "使用本软件的个人或机构。"
        )
        text_box = ctk.CTkTextbox(step0, width=620, height=330, wrap="word",
                                    font=ctk.CTkFont(size=16))
        text_box.pack(padx=10, pady=(0, 8))
        text_box.insert("end", disclaimer_text)
        text_box.configure(state="disabled")

        # 第1步：程序介绍
        step1 = wizard_tabs.add("1. 介绍")
        ctk.CTkLabel(step1, text="DETEQX 使用向导",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step1, text="基于 SALDI 质谱脂质指纹技术，结合机器学习，实现疾病样本的智能分类分析。",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(pady=3)
        ctk.CTkLabel(step1, text="（科研用途，非医疗器械）",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(pady=3)
        ctk.CTkLabel(step1, text="核心流程：数据预处理  →  模型训练与评估  →  新样本预测",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(pady=3)
        ctk.CTkLabel(step1, text="设计理念：",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', padx=20, pady=(10, 2))
        ctk.CTkLabel(step1, text="• 样本级归一化（Max/Sum/Median），消除批次技术变异，无数据泄露",
                     wraplength=600, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=30, pady=1)
        ctk.CTkLabel(step1, text="• 交叉验证采用 RepeatedStratifiedKFold（5折×20次），设计参考医疗 AI 规范",
                     wraplength=600, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=30, pady=1)
        ctk.CTkLabel(step1, text="• 所有评估指标含 95% 置信区间，结果可重现（固定随机种子）",
                     wraplength=600, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=30, pady=1)
        ctk.CTkLabel(step1, text="• 多项目隔离管理，每个任务独立存储数据、模型与报告",
                     wraplength=600, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=30, pady=1)

        # 第2步：数据预处理
        step2 = wizard_tabs.add("2. 数据预处理")
        ctk.CTkLabel(step2, text="数据预处理步骤",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step2, text="1. 点击'数据预处理'按钮，打开文件分类窗口",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="2. 在弹出窗口中自定义两个类别的名称",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="3. 分别选择包含两类样本的文件夹",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="4. 确认预览信息，开始处理生成CSV文件",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step2, text="5. 等待智能峰发现处理完成，生成CSV文件",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        # 第3步：模型训练
        step3 = wizard_tabs.add("3. 模型训练")
        ctk.CTkLabel(step3, text="模型训练与评估",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step3, text="1. 点击 '选择整理好的 .csv 文件' 按钮，选择预处理生成的data_xxx.csv 文件",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=(4, 0))
        ctk.CTkLabel(step3, text="2. 从菜单栏选择机器学习算法（默认推荐 PLSRegression）",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=(4, 0))
        ctk.CTkLabel(step3, text="3. 点击 '开始训练'，进行 5折×20次 共100轮交叉验证，训练期间按钮显示「训练中…」",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=(4, 0))
        ctk.CTkLabel(step3, text="4. 训练完成后自动生成 ROC 曲线、混淆矩阵等评估图表",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=(4, 0))
        ctk.CTkLabel(step3, text="⚠ 如需中止训练：点击菜单栏 ⟲ 重置按钮，立即终止并复位界面",
                     wraplength=640, text_color="gray", font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=(10, 2))

        # 第4步：样本预测
        step4 = wizard_tabs.add("4. 样本预测")
        ctk.CTkLabel(step4, text="新样本预测",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(step4, text="1. 模型训练完成后，点击 '选择要检测的txt文件' 按钮",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="2. 选择要分析的未知样本txt文件",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="3. 查看预测结果及自定义类别的概率分布",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)
        ctk.CTkLabel(step4, text="4. 可点击 '查看模型详情' 了解模型参数",
                     wraplength=640, font=ctk.CTkFont(size=15)).pack(anchor='w', padx=20, pady=2)

        # 底部按钮
        button_frame = ctk.CTkFrame(self.wizard_window, fg_color="transparent")
        button_frame.pack(fill='x', padx=10, pady=10)

        ctk.CTkCheckBox(button_frame, text="启动时显示此向导",
                        variable=show_again_var).pack(side='left')
        ctk.CTkButton(button_frame, text="我已知晓免责声明，开始使用",
                      command=close_wizard).pack(side='right')


    def show_about(self):
        """显示关于信息"""
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("关于")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        set_window_icon(about_window)
        about_window.geometry("350x600")
        center_window(about_window, 350, 600)

        # ===== 软件名称 =====
        ctk.CTkLabel(
            about_window,
            text="🔬 DETEQX",  # 改成喜欢的
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(30, 5))
        
         # ===== Logo 图片 =====
        image_path = ICON_CONFIG.get('app_icon_png')
        if image_path:
            try:
                logo_image = ctk.CTkImage(
                    light_image=Image.open(image_path),
                    dark_image=Image.open(image_path),
                    size=(80, 80)  # 调整大小
                )
                ctk.CTkLabel(
                    about_window,
                    image=logo_image,
                    text=""  # 不显示文字
                ).pack(pady=(25, 10))
            except Exception:
                pass  # 图片加载失败就跳过

        # ===== 一句话介绍 =====
        ctk.CTkLabel(
            about_window,
            text="随便写点什么slogan",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack()
        
        # ===== 版本 =====
        ctk.CTkLabel(
            about_window,
            text="v1.9.12.2",
            font=ctk.CTkFont(size=11)
        ).pack(pady=(20, 5))
        
        # ===== 正文区域（随便写）=====
        content = """
    这里随便写点什么

    可以是项目介绍
    可以是碎碎念
    可以是致谢
    可以是彩蛋 🥚

    总之想写啥写啥
        """
        
        ctk.CTkLabel(
            about_window,
            text=content.strip(),
            font=ctk.CTkFont(size=11),
            justify="center"
        ).pack(pady=20)
        
        # ===== 底部署名 =====
        ctk.CTkLabel(
            about_window,
            text="by 邱成桐(负责想法)  claude(负责实现) 和 陶鉴（负责划水）· 2026",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(pady=(10, 0))
        
        # ===== 底部 Logo =====
        frame2_path = get_resource_path('assets/Frame 2.png')
        try:
            frame2_image = ctk.CTkImage(
                light_image=Image.open(frame2_path),
                dark_image=Image.open(frame2_path),
                size=(60, 60)
            )
            ctk.CTkLabel(
                about_window,
                image=frame2_image,
                text=""
            ).pack(pady=(5, 0))
        except Exception:
            pass

        # ===== 关闭按钮 =====
        ctk.CTkButton(
            about_window,
            text="好的",
            width=80,
            command=about_window.destroy
        ).pack(pady=20)

        #
        _egg_buf = []
        _egg_code = list("swws50")

        def _on_key(event):
            _egg_buf.append(event.char)
            if len(_egg_buf) > len(_egg_code):
                _egg_buf.pop(0)
            if _egg_buf == _egg_code:
                _egg_buf.clear()
                _show_easter_egg(about_window)

        about_window.bind("<Key>", _on_key)


def _show_easter_egg(parent):
    """彩蛋弹窗"""
    egg = ctk.CTkToplevel(parent)
    egg.title("ecust的swws50本人")
    egg.resizable(False, False)
    egg.transient(parent)
    egg.grab_set()
    egg.geometry("280x440+20+20")

    try:
        ico_path = get_resource_path('assets/Frame 2.ico')
        egg.iconbitmap(ico_path)
        egg.after(200, egg.iconbitmap, ico_path)
    except Exception:
        pass

    ctk.CTkLabel(
        egg,
        text="是的，这回真的是本人了",
        font=ctk.CTkFont(size=20, weight="bold")
    ).pack(pady=(30, 10))

    ctk.CTkLabel(
        egg,
        text='''《今夜》\n🎶今夜我只想说些碎碎念🎶\n🎶倾听为项目奔波的憔悴🎶\n🎶就让我再一次 嘟嘟囔囔🎶\n🎶找寻点小确幸 慰藉我🎶
🎶让我为这项目肝到天明吧🎶\n🎶好想抱着键盘 轻轻旋转🎶\n🎶就让我歇一下🎶\n🎶就歇一下🎶\n🎶明天又要说 好的老师🎶\n💃💃💃
        \n\n什么，你说那里有三只小猪？\n不，孩子，那是我的队友\n不不不，这儿不是监狱，这是我来时路\n你知道的，能力越大，能力越来越大\n……''',
        font=ctk.CTkFont(size=12),
        justify="center",
        text_color="gray"
    ).pack(pady=10)

    ctk.CTkButton(
        egg,
        text="悄悄关掉",
        width=100,
        command=egg.destroy
    ).pack(pady=20)
