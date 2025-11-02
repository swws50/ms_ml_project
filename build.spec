# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 应用程序信息
app_name = 'DETEQX'
app_version = '1.9.5.3.6'
main_script = 'src/main.py'

a = Analysis(
    [main_script],
    pathex=['src'],  # 添加src路径
    binaries=[],
    datas=[
        (os.path.abspath('assets/app_icon.ico'), 'assets'),
        (os.path.abspath('assets/app_icon.png'), 'assets'),
        
        # 包含所有必要的Python文件
        ('src/config.py', 'src'),
        ('src/utils.py', 'src'),
        ('src/validation_decorators.py', 'src'),
        ('src/data_store.py', 'src'),
        ('src/data_preprocessor.py', 'src'),
        ('src/data_processing.py', 'src'),
        ('src/feature_detector.py', 'src'),
        ('src/model_training.py', 'src'),
        ('src/model_predictor.py', 'src'),
        ('src/output_manager.py', 'src'),
        ('src/print_manager.py', 'src'),
        ('src/visualization.py', 'src'),
        ('src/ui_components.py', 'src'),
        ('src/parameter_tuning_window.py', 'src'),
        ('src/automated_workflow.py', 'src'),
        ('src/project_manager.py', 'src'),
        ('src/help_system.py', 'src'),
        # 注意：main.py 不需要在 datas 中，因为它已经是主脚本
    ],
    hiddenimports=[
        # tkinter 相关
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',

        # customtkinter 相关
        'customtkinter',
        'customtkinter.windows.widgets.core_widget_classes',
        'customtkinter.windows.ctk_tk',
        'customtkinter.windows.ctk_theme',
        
        # 数据科学相关
        'pandas',
        'numpy',
        'scipy',
        'scipy.sparse.csgraph',
        'scipy.special',
        
        # sklearn 相关 - 修复拼写错误
        'sklearn',
        'sklearn.ensemble',
        'sklearn.model_selection',
        'sklearn.metrics',
        'sklearn.preprocessing',
        'sklearn.tree',
        'sklearn.neighbors',
        'sklearn.svm',
        'sklearn.linear_model',  # 修正：sklinear_model → sklearn.linear_model
        'sklearn.utils',
        'sklearn.utils._weight_vector',
        'sklearn.exceptions',
        
        # 科学计算
        'pyopenms',
        
        # 可视化
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.backends.backend_agg',
        'matplotlib._path',
        'matplotlib._png',
        'matplotlib.backends._backend_tk',
        
        # PDF 生成
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',

        # 其他必要库
        'joblib',
        'tqdm',
        'threading',
        'queue',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pathlib',
        'collections',
        'itertools',
        'functools',
        'concurrent',
        'concurrent.futures',
        
        # 可能的额外依赖
        'importlib',
        'importlib.resources',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],  # 暂时移除 runtime_hook，先测试基本功能
    excludes=[
        # 排除不必要的模块以减少体积
        'torch', 'tensorflow', 'keras',
        'numba', 'llvmlite',
        'ipykernel', 'jupyter', 'notebook',
        'sphinx', 'docutils',
        'spyder',
        'pytest', 
        'setuptools', 'pip',
        'pywin32', 'pywin32_system32',
        'paramiko', 'cryptography',
        'zmq', 
        'distributed', 'dask',
        # 排除测试文件
        'matplotlib.tests', 'scipy.tests', 'numpy.tests', 'sklearn.tests'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 可执行文件配置
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 保持 True 便于调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.abspath('assets/app_icon.ico'),
)