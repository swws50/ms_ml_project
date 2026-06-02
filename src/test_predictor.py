# test_predictor.py - 预测管道测试脚本
# 运行方式：在 src 目录下执行 python test_predictor.py

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from joblib import load

BUNDLE_PATH  = r"C:\Users\wj611\Desktop\大创\程序\outputs\测试-2026-6-2 20.06\models\PLSRegression_20260602_2008.joblib"
RAW_DATA_DIR = r"C:\Users\wj611\Desktop\大创\程序\raw_data\第一批"
MZ_TOLERANCE = 0.2

# 每类各取 3 个样本做预测质量测试
HC_SAMPLES = ["HC_C11.txt", "HC_D1.txt", "HC_E1.txt"]
LC_SAMPLES = ["LC_E16.txt", "LC_F1.txt", "LC_G2.txt"]

SEP = "-" * 60


def load_bundle():
    print(SEP)
    print("【测试1】Bundle 结构检查")
    bundle = load(BUNDLE_PATH)
    required_keys = ["model", "training_features", "normalization_method",
                     "log_transform", "scaling_method",
                     "pareto_means", "pareto_stds", "half_min_values"]
    for k in required_keys:
        val = bundle.get(k)
        if val is None:
            status = "❌ 缺失（需重新训练）"
        elif isinstance(val, list):
            status = f"✓  长度={len(val)}"
        elif isinstance(val, dict):
            status = f"✓  条目数={len(val)}"
        else:
            status = f"✓  值={val}"
        print(f"  {k:25s}: {status}")
    return bundle


def test_consistency(bundle):
    """手动重现变换链，与 FeatureDetector 输出逐元素对比"""
    print(SEP)
    print("【测试2】变换链数值一致性")

    test_file = os.path.join(RAW_DATA_DIR, HC_SAMPLES[0])
    if not os.path.exists(test_file):
        print(f"  跳过：找不到 {test_file}")
        return

    training_mz   = bundle.get("training_features", [])
    norm_method   = bundle.get("normalization_method")
    log_transform = bundle.get("log_transform", False)
    scaling       = bundle.get("scaling_method")
    pareto_means  = bundle.get("pareto_means")
    pareto_stds   = bundle.get("pareto_stds")
    half_min_vals = bundle.get("half_min_values", {})

    # --- 手动变换链 ---
    raw = pd.read_csv(test_file, sep=r'\s+', header=None)
    intensities = raw.iloc[:, 1]
    norm_factor = float(intensities.agg(norm_method)) if norm_method else 1.0

    manual = []
    for mz in training_mz:
        mask = (raw.iloc[:, 0] >= mz - MZ_TOLERANCE) & (raw.iloc[:, 0] <= mz + MZ_TOLERANCE)
        val = float(raw[mask].iloc[:, 1].max()) if mask.any() else 0.0
        if val == 0.0:
            hm = half_min_vals.get(str(mz))
            if hm is not None:
                val = hm
        val = val / norm_factor if norm_factor > 0 else val
        manual.append(val)

    arr = np.array(manual, dtype=float)
    if log_transform:
        arr = np.log2(arr + 1)
    if scaling == 'pareto' and pareto_means and pareto_stds:
        means = np.array(pareto_means)
        stds  = np.where(np.array(pareto_stds) == 0, 1.0, np.array(pareto_stds))
        arr   = (arr - means) / np.sqrt(stds)

    # --- FeatureDetector 输出 ---
    from data_processing import FeatureDetector
    fd = FeatureDetector()
    fd.training_features    = training_mz
    fd.normalization_method = norm_method
    fd.log_transform        = log_transform
    fd.scaling_method       = scaling
    fd.pareto_means         = pareto_means
    fd.pareto_stds          = pareto_stds
    fd.half_min_values      = half_min_vals

    auto = fd.process_prediction_sample(test_file, training_mz, norm_method).flatten()

    max_err = np.abs(arr - auto).max()
    mean_err = np.abs(arr - auto).mean()
    print(f"  样本: {HC_SAMPLES[0]}")
    print(f"  特征数: {len(arr)}")
    print(f"  最大误差: {max_err:.2e}  均值误差: {mean_err:.2e}")
    if max_err < 1e-8:
        print("  ✓  变换链完全一致")
    else:
        print("  ❌  变换链存在偏差，需排查")


def test_prediction_quality(bundle):
    """预测已知样本，检查正确率和概率区分度"""
    print(SEP)
    print("【测试3】预测质量（训练集已知样本）")

    # 把 bundle 状态注入 PredictionManager（跳过磁盘加载，直接用内存 bundle）
    import data_store
    from data_processing import FeatureDetector
    from model_predictor import PredictionManager

    # 构造一个预设好状态的 manager（绕过 load_model 里的文件扫描）
    mgr = PredictionManager()
    mgr.model = bundle["model"]
    mgr.pls_threshold = bundle.get("pls_threshold")
    fd = mgr.feature_detector
    fd.training_features    = bundle.get("training_features")
    fd.normalization_method = bundle.get("normalization_method")
    fd.log_transform        = bundle.get("log_transform", False)
    fd.scaling_method       = bundle.get("scaling_method")
    fd.pareto_means         = bundle.get("pareto_means")
    fd.pareto_stds          = bundle.get("pareto_stds")
    fd.half_min_values      = bundle.get("half_min_values", {})

    # class_manager 需要知道类别名
    from data_store import class_manager
    class_manager.set_names("类别0", "类别1")

    samples = (
        [(f, "类别0") for f in HC_SAMPLES] +
        [(f, "类别1") for f in LC_SAMPLES]
    )

    correct = 0
    probs_all = []

    print(f"  {'文件':20s} {'真实':6s} {'预测':6s} {'最大概率':8s} {'通过'}")
    print(f"  {'-'*55}")

    for fname, true_label in samples:
        fpath = os.path.join(RAW_DATA_DIR, fname)
        if not os.path.exists(fpath):
            print(f"  {fname:20s}  跳过（文件不存在）")
            continue

        # 直接调用 process_prediction_sample + get_prediction_probability
        try:
            feats = fd.process_prediction_sample(fpath)
            pred_int, probs = mgr.get_prediction_probability(feats)
            pred_label = class_manager.decode(pred_int)
            max_prob = float(probs.max())
            probs_all.append(max_prob)
            ok = "✓" if pred_label == true_label else "❌"
            if pred_label == true_label:
                correct += 1
            print(f"  {fname:20s} {true_label:6s} {pred_label:6s} {max_prob:.4f}   {ok}")
        except Exception as e:
            print(f"  {fname:20s}  错误: {e}")

    n = len(probs_all)
    if n:
        print(f"\n  正确率: {correct}/{n}  ({correct/n:.0%})")
        print(f"  概率均值: {np.mean(probs_all):.4f}  最小: {np.min(probs_all):.4f}")
        if np.mean(probs_all) < 0.55:
            print("  ⚠️  概率均值偏低（接近0.5），变换链可能未正确生效")
        else:
            print("  ✓  概率区分度正常")


def test_backward_compat():
    """旧格式 bundle（缺少新 key）不应崩溃"""
    print(SEP)
    print("【测试4】旧 Bundle 向后兼容")
    from joblib import dump
    import tempfile

    orig = load(BUNDLE_PATH)
    old_bundle = {"model": orig["model"], "training_features": orig["training_features"]}
    tmp = tempfile.mktemp(suffix=".joblib")
    dump(old_bundle, tmp)

    try:
        from model_predictor import PredictionManager
        mgr = PredictionManager()
        mgr.temp_model_path = tmp
        mgr.load_model()
        print(f"  ✓  旧格式加载成功，log_transform={mgr.feature_detector.log_transform}")
    except Exception as e:
        print(f"  ❌  加载失败: {e}")
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    bundle = load_bundle()
    test_consistency(bundle)
    test_prediction_quality(bundle)
    test_backward_compat()
    print(SEP)
    print("测试完成")
    print()
    print("注意：此 bundle 是代码修改前生成的，缺少新 key 属于正常现象。")
    print("重新跑一次【预处理 → 训练】后生成的 bundle 才会包含完整参数。")
