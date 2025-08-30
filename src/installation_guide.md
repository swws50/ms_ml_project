# 诊断分析工具 - 安装说明

## 系统要求

- **操作系统**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM（推荐 8GB 以上）
- **存储空间**: 至少 2GB 可用空间
- **显示器**: 分辨率至少 1280x800

## 安装步骤

### 1. 检查Python环境

首先确认你的Python版本：

```bash
python --version
# 或者
python3 --version
```

如果Python版本低于3.8，请先升级Python。

### 2. 创建虚拟环境（推荐）

创建独立的Python环境以避免依赖冲突：

```bash
# Windows
python -m venv diagnostic_env
diagnostic_env\Scripts\activate

# macOS/Linux
python3 -m venv diagnostic_env
source diagnostic_env/bin/activate
```

### 3. 更新pip

确保使用最新版本的pip：

```bash
python -m pip install --upgrade pip
```

### 4. 安装依赖库

#### 方式1：使用requirements.txt（推荐）

```bash
pip install -r requirements.txt
```

#### 方式2：手动安装核心依赖

如果requirements.txt安装失败，可以尝试逐个安装：

```bash
# GUI框架
pip install customtkinter>=5.2.0

# 基础科学计算
pip install numpy>=1.21.0 pandas>=1.3.0

# 机器学习
pip install scikit-learn>=1.0.0 joblib>=1.1.0

# 数据可视化
pip install matplotlib>=3.5.0

# 图像处理
pip install Pillow>=8.3.0

# 进度条
pip install tqdm>=4.62.0

# 质谱数据处理（关键依赖）
pip install pyopenms>=2.8.0
```

### 5. 特殊依赖安装说明

#### pyOpenMS（质谱数据处理）

pyOpenMS是本项目的核心依赖，用于质谱数据处理。如果安装遇到问题：

**Windows用户**：
```bash
# 如果直接安装失败，尝试使用conda
conda install -c bioconda pyopenms

# 或者使用预编译包
pip install --find-links https://abibuilder.cs.uni-tuebingen.de/archive/openms/pyOpenMS/releases/
```

**macOS用户**：
```bash
# 可能需要安装Xcode命令行工具
xcode-select --install

# 然后安装pyOpenMS
pip install pyopenms
```

**Linux用户**：
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential cmake

# 然后安装pyOpenMS
pip install pyopenms
```

## 验证安装

创建测试文件 `test_install.py`：

```python
#!/usr/bin/env python3
# test_install.py - 验证安装

def test_imports():
    """测试关键模块导入"""
    try:
        import customtkinter as ctk
        print("✓ CustomTkinter")
        
        import numpy as np
        print("✓ NumPy")
        
        import pandas as pd
        print("✓ Pandas")
        
        import sklearn
        print("✓ Scikit-learn")
        
        import pyopenms as oms
        print("✓ PyOpenMS")
        
        import matplotlib.pyplot as plt
        print("✓ Matplotlib")
        
        from PIL import Image
        print("✓ Pillow")
        
        import joblib
        print("✓ Joblib")
        
        print("\n所有依赖库安装成功！")
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("正在检查依赖库...")
    if test_imports():
        print("\n可以运行主程序了:")
        print("python main.py")
    else:
        print("\n请检查依赖库安装")
```

运行验证：

```bash
python test_install.py
```

## 运行程序

安装完成后，运行主程序：

```bash
python main.py
```

## 可选组件

### Excel文件支持（可选）

如果需要处理Excel文件：

```bash
pip install openpyxl>=3.0.0
```

### 高级数值计算（可选）

```bash
pip install scipy>=1.7.0
```

## 创建图标文件

程序需要图标文件。在项目根目录创建以下文件结构：

```
assets/
├── app_icon.ico    # Windows图标
└── app_icon.png    # 通用图标

# 或者直接在根目录放置
icon.ico            # 后备图标
```

## 故障排除

### 常见问题

#### 1. CustomTkinter导入错误

```bash
# 确保版本正确
pip uninstall customtkinter
pip install customtkinter>=5.2.0
```

#### 2. PyOpenMS安装失败

**Windows**: 尝试使用conda或预编译包
**macOS**: 确保安装了Xcode命令行工具
**Linux**: 确保安装了构建工具

#### 3. 图标显示异常

- 检查图标文件路径是否正确
- 确保图标文件格式正确（ICO/PNG）
- 检查文件权限

#### 4. 内存不足错误

- 减少训练迭代次数（修改config.py中的TRAINING_ITERATIONS）
- 关闭其他占用内存的程序
- 考虑增加系统内存

### 获取帮助

如果遇到安装问题：

1. 检查Python版本是否符合要求
2. 确保网络连接正常
3. 尝试使用不同的pip镜像源：

```bash
# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 使用阿里镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 开发环境搭建（可选）

如果需要修改代码或开发新功能：

```bash
# 安装开发工具
pip install pytest>=6.0.0 black>=21.0.0 flake8>=3.9.0

# 运行测试
pytest tests/

# 代码格式化
black *.py

# 代码质量检查
flake8 *.py
```

## 卸载

如果需要完全卸载：

```bash
# 退出虚拟环境（如果使用了）
deactivate

# 删除虚拟环境文件夹
# Windows
rmdir /s diagnostic_env

# macOS/Linux
rm -rf diagnostic_env

# 或者在当前环境中卸载所有包
pip uninstall -r requirements.txt -y
```

---

**注意**: 首次运行可能需要下载一些数据模型，请保持网络连接。程序会在outputs目录下创建必要的文件夹结构。