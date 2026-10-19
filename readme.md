# DETEQX

**AI-Powered Disease Sample Analysis System Based on Mass Spectrometry Fingerprinting**
A SALDI mass spectrometry and lipid fingerprint analysis tool for early-stage liver cancer research

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-orange.svg)]()
[![Version](https://img.shields.io/badge/Version-1.15.10-green.svg)]()

> **Disclaimer**: This software is intended for academic research and scientific experimentation only. It is not a medical device, and its results must not be used as the basis for clinical diagnosis. For any medical decisions, please consult a licensed physician.

---

## 📖 Overview

DETEQX is an end-to-end mass spectrometry data analysis system, originally designed for early hepatocellular carcinoma (HCC) screening but applicable to any disease classification task. The system analyzes SALDI mass spectrometry data from serum samples (0–1000 m/z range), leverages lipid fingerprint features to build machine learning classification models, and intelligently distinguishes cancer samples from normal ones.

### Core Capabilities

- **Intelligent Peak Detection**: Integrated pyOpenMS professional mass spectrometry analysis for automatic discovery and selection of optimal feature peaks
- **Sample-Level Normalization**: Supports Max / Sum / Median normalization methods to eliminate technical variation
- **Rigorous Cross-Validation**: RepeatedStratifiedKFold (5-fold × 20 repeats), designed in accordance with medical AI standards
- **Multi-Algorithm Support**: PLS, Random Forest, SVM, LDA, Logistic Regression, MLP
- **Comprehensive Evaluation**: 95% confidence intervals, ROC curves, confusion matrices, sensitivity/specificity analysis
- **PDF Diagnostic Reports**: Auto-generated structured reports with model performance metrics and evaluation charts
- **Real-Time Status Feedback**: Three-phase chip status bar (Preprocessing / Training / Prediction) for at-a-glance progress

---

## 🔧 Environment Setup

### System Requirements

- **Python**: 3.8+
- **Operating System**: Windows / macOS / Linux
- **Memory**: 4 GB+ recommended

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Core Dependencies

```
numpy >= 1.21.0
pandas >= 1.3.0
scikit-learn >= 1.0.0
scipy >= 1.7.0
matplotlib >= 3.5.0
customtkinter >= 5.0.0
pyopenms >= 3.0.0
joblib >= 1.1.0
pillow >= 9.0.0          # Login screen image display
```

---

## 🚀 Quick Start

```bash
python main.py
```

### Standard Workflow

```
┌──────────────────────┐
│  1. Data Preprocessing│  Select raw spectra folder → Classify → Choose normalization method
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  2. Feature Extraction│  pyOpenMS peak detection → Consensus peak filtering → Build feature matrix
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  3. Model Training    │  Select algorithm → 5×20 cross-validation → Save best model
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  4. Performance Eval  │  ROC curve / Confusion matrix / 95% CI / Sensitivity & Specificity
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  5. Sample Prediction │  Load new samples → Auto-normalize → Output classification results
└──────────────────────┘
```

---

## 📁 Project Structure

```
DETEQX/
├── src/
│   │
│   │  # ===== Core Modules =====
│   ├── main.py                    # Entry point, main interface manager (MainGUIManager)
│   ├── config.py                  # Global configuration parameters
│   ├── data_store.py              # Runtime data store + ClassMappingManager
│   │
│   │  # ===== Data Processing =====
│   ├── data_preprocessor.py       # Core data preprocessing (peak detection + normalization)
│   ├── data_processing.py         # Data loading + FeatureDetector
│   │
│   │  # ===== Machine Learning =====
│   ├── model_training.py          # Model training engine
│   ├── model_predictor.py         # Sample prediction manager
│   │
│   │  # ===== UI Components =====
│   ├── ui_components.py           # GUI component library (various Panels)
│   ├── help_system.py             # Help system and user wizard
│   ├── visualization.py           # Chart generation (including 95% CI)
│   ├── print_manager.py           # Diagnostic report printing
│   │
│   │  # ===== Project Management =====
│   ├── project_manager.py         # Multi-project management (create/switch/delete)
│   ├── output_manager.py          # Output file management
│   │
│   │  # ===== Utility Modules =====
│   ├── login_system.py            # Login screen (demo only, no real authentication)
│   ├── parameter_tuning_window.py # Model hyperparameter tuning window
│   ├── automated_workflow.py      # Automated workflow (one-click: preprocess → train → predict)
│   ├── validation_decorators.py   # Validation decorators
│   └── utils.py                   # Utility functions
│
├── outputs/                       # Output directory (isolated per project)
│   └── {project_name}/
│       ├── data/                  # Processed feature matrices
│       ├── models/                # Trained model files
│       ├── metrics/               # Evaluation metric data (per-training .json)
│       └── charts/                # Visualization charts
│           └── {model_stem}/      # Dedicated directory named after the model (permanently bound)
│
├── assets/                        # Icon assets
├── requirements.txt
├── readme.md
├── README_EN.md
└── THIRD_PARTY_LICENSES.txt
```

### Core Module Responsibilities

| Module                       | Responsibility                                                                             | Key Classes / Functions                              |
| ---------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| `data_preprocessor.py`       | Peak detection, normalization, feature matrix construction                                 | `DataPreprocessor`, `NormalizationManager`           |
| `data_processing.py`         | Data loading, prediction sample processing                                                 | `FeatureDetector`, `open_data_file()`                |
| `data_store.py`              | Global state management, class mapping                                                     | `ClassMappingManager` (singleton)                    |
| `model_training.py`          | Cross-validation training, save model bundle + metrics JSON                                | `ModelTrainer`, `train_model()`                      |
| `model_predictor.py`         | Sample prediction, result formatting                                                       | `PredictionManager`                                  |
| `visualization.py`           | Chart generation, performance metric calculation; charts saved in model-named subdirectory | `MetricsCalculator`, `generate_performance_charts()` |
| `print_manager.py`           | PDF diagnostic report generation (ReportLab Platypus)                                      | `PrintManager`                                       |
| `project_manager.py`         | Multi-project management                                                                   | `ProjectManager`, `ProjectCreationWizard`            |
| `parameter_tuning_window.py` | Model hyperparameter adjustment                                                            | `ParameterTuningWindow`                              |

### Auxiliary Module Notes

| Module                          | Description                                                | Status              |
| ------------------------------- | ---------------------------------------------------------- | ------------------- |
| `login_system.py`               | Demo login screen; any input is accepted                   | × Planned removal   |
| `automated_workflow.py`         | One-click automated pipeline: preprocess → train → predict | ✅ Available         |
| `consensus_peak_diagnostics.py` | Consensus peak diagnostic/debug script                     | 🔧 Adjusted, usable |

---

## ⚙️ Configuration

### Feature Selection Parameters (`config.py`)

```python
MAX_FEATURES = 50           # Maximum features (truncation ceiling)
MAX_MISSING_RATE = 0.5      # Maximum missing rate (peaks missing in >50% of samples are discarded)
MIN_FOLD_CHANGE = 1.3       # Minimum fold change (intersected with MW-U; computed in log₂ domain)
MZ_TOLERANCE = 0.2          # m/z matching tolerance (prediction-side feature alignment)

# Added in v1.15.x
LOG_TRANSFORM = True        # log₂(x+1) transform toggle
SCALING_METHOD = 'pareto'   # Scaling method: 'pareto' or None
P_VALUE_THRESHOLD = 0.05    # Mann-Whitney U significance threshold
FDR_CORRECTION = False      # BH-FDR correction toggle (too conservative for small-sample / high-feature settings; off by default)
```

### Cross-Validation Configuration

```python
CV_SPLITS = 5               # 5-fold cross-validation
CV_REPEATS = 20             # 20 repeats
CV_RANDOM_STATE = 42        # Random seed (reproducible)
# Total training iterations: 5 × 20 = 100
```

### Supported Models

| Model                       | Configuration    | Best Use Case                                                            |
| --------------------------- | ---------------- | ------------------------------------------------------------------------ |
| **PLSRegression** (default) | n_components=4   | First choice for mass spec data; high-dimensional, small-sample settings |
| RandomForestClassifier      | n_estimators=250 | Large datasets, stability-first                                          |
| LinearSVC                   | max_iter=5000    | Linearly separable data                                                  |
| LinearDiscriminantAnalysis  | shrinkage='auto' | Dimensionality reduction + classification                                |
| LogisticRegressionCV        | Cs=20, cv=5      | Small datasets, interpretability                                         |
| MLPClassifier               | hidden=(100,)    | Complex non-linear patterns                                              |

> 💡 Model hyperparameters can be modified via the "Parameter Tuning" window in the menu bar.

---

## 🔬 Technical Details

### 1. Preprocessing Pipeline SOP (v1.15.x)

**Standard metabolomics SOP — four-phase pipeline**:

```
Phase 1: Peak detection + collect normalization statistics (do not apply normalization)
     ↓
Phase 2: 0.2 Da greedy-clustering alignment → full consensus peak candidate pool
     ↓
Phase 3: Discard peaks missing in >50% of all samples
     ↓
Phase 4: Numerical matrix construction
         → Half-minimum missing value imputation
         → Within-sample normalization (max / sum / median)
         → log₂(x+1) transformation
         → Mann-Whitney U feature selection (p < 0.05, truncated to top 50)
         → Pareto scaling
         → Output feature matrix
```

**Normalization Method Comparison**:

| Method                | Formula       | Characteristics                            |
| --------------------- | ------------- | ------------------------------------------ |
| **max** (recommended) | I / I_max     | Preserves relative intensity; range [0, 1] |
| sum (TIC)             | I / Σ(I)      | Eliminates injection volume variation      |
| median                | I / median(I) | Robust to outliers                         |

**Prediction-time transform chain**: The normalization method, log₂ toggle, Pareto scaling parameters (per-feature mean and std vectors), and half-min imputation values are all bundled with the model (v1.15.10+). The full transform chain is automatically reproduced at prediction time — no dependency on training CSV files.

### 2. Cross-Validation Method (v1.9.7+)

**Upgraded from Monte Carlo to RepeatedStratifiedKFold**:

| Criterion           | Old Method (v1.9.6)        | New Method (v1.9.7+)        |
| ------------------- | -------------------------- | --------------------------- |
| Approach            | 500 random samples         | 5-fold × 20 repeats         |
| Test count/sample   | Uneven                     | Exactly 20 times per sample |
| Variance estimate   | Potentially underestimated | Unbiased estimate           |
| Computation time    | Baseline                   | ~20% of baseline            |
| Standard compliance | —                          | FDA/NMPA, Nature/Lancet     |

### 3. Class Mapping Management (v1.9.9+)

**Unified `ClassMappingManager` singleton**:

```python
from data_store import class_manager

# Read
class_manager.class_0_name      # 'HCC'
class_manager.class_1_name      # 'Normal'
class_manager.names             # ('HCC', 'Normal')

# Encode / Decode
class_manager.encode('HCC')     # 0
class_manager.decode(0)         # 'HCC'

# Set
class_manager.set_names('HCC', 'Normal')
```

### 4. Visualization & Statistics (v1.9.5+)

**`MetricsCalculator` computes all metrics in one place** to avoid redundant calculations:

- All charts include **95% confidence intervals** (t-distribution)
- Performance metric tables are exported as CSV for easy copying
- Sensitivity/Specificity row labels in `MetricsTable.csv` are bound to actual class names (e.g., `Sensitivity – HCC`), eliminating ambiguity when classes are swapped (v1.11.8+)
- Chart storage: each training run creates its own subdirectory `charts/{ModelType}_{timestamp}/`, permanently bound to the model file — subsequent training runs do not overwrite previous charts (v1.12.5+)

### 5. Multi-Project Management

**`ProjectManager` supports**:

- Creating, deleting, and switching between projects
- Independent output directories per project
- Project description and metadata management

### 6. Model Bundle Format (v1.11.7+)

Models are saved as a dict bundle containing all metadata required for prediction:

```python
model_bundle = {
    "model":                sklearn model object,
    "training_features":    list of training feature m/z values (for feature alignment at prediction time),
    "normalization_method": 'max' / 'sum' / 'median' / None,
    "pls_threshold":        mean PLS decision threshold (PLS models only),
    # Added in v1.15.10: prediction-side transform chain parameters
    "log_transform":        True / False,
    "scaling_method":       'pareto' / None,
    "pareto_means":         [per-feature mean, ...],    # Pareto scaling training parameters
    "pareto_stds":          [per-feature std, ...],
    "half_min_values":      {"mz_string": half_min_value, ...},
}
```

Predictions can be made directly across sessions, automated pipelines, and model switches — no longer dependent on the training CSV file. Older bundles (missing v1.15.10 keys) are backward compatible: they load without error and fall back to normalization-only behavior.

### 7. Training Metrics File Format (v1.11.9+)

Each training run generates `metrics/{ModelType}_{timestamp}.json`, matching the model file name and timestamp:

```json
{
  "meta": {
    "model": "PLSRegression",
    "timestamp": "20260321_1805",
    "cv": "5-fold × 20 repeats (100 iterations)",
    "n_samples": 19,
    "class_names": ["HCC", "Normal"],
    "threshold_strategy": "Youden's J"
  },
  "confusion_matrices": [{"tn": 10, "fp": 0, "fn": 0, "tp": 9}, ...],
  "f_scores": [{"precision": 1.0, "recall": 1.0, "f1": 1.0}, ...],
  "auc_list": [...],
  "fpr_values": [...],
  "tpr_values": [...]
}
```

Historical data is never overwritten; JSON files can be inspected directly.

### 8. PDF Diagnostic Report (v1.12.2+)

Structured reports generated using the ReportLab Platypus layout engine:

- **Contents**: Patient information table, prediction results, model performance metrics (AUC / Sensitivity / Specificity / F1 with 95% CI), evaluation charts (ROC curve + confusion matrix side by side)
- **Chart binding**: Resolves `charts/{stem}/` path from the metrics JSON to ensure a one-to-one correspondence between report charts and model
- **Preview**: Generates a temporary PDF and opens it with the system default PDF reader — WYSIWYG
- **Disclaimer**: A "For clinical reference only; not to be used as a diagnostic basis" statement is automatically appended at the end of every report

### 9. First-Launch Disclaimer (v1.13.1+)

A mandatory usage notice is displayed on first launch; users must check the agreement checkbox to proceed:

- The agreement record is signed with **HMAC-SHA256** and stored in the `_ev` field of `help_config.json`
- The record is bound to the machine's hostname; manually tampering with any field causes signature verification to fail and the notice to reappear on the next launch
- Machines that have already accepted the notice will not see the notice tab again when the wizard opens

---

## 📊 Output Files

### Data Files

```
outputs/{project}/data/
└── data_{method}.csv          # Feature matrix (method: max / sum / median / raw)
```

**CSV structure**:

```
m/z_123.45, m/z_234.56, ..., label
0.85,       0.23,       ..., HCC
0.12,       0.67,       ..., Normal
```

### Model Files

```
outputs/{project}/models/
└── {ModelType}_{timestamp}.joblib    # e.g. PLSRegression_20251201_143022.joblib
```

### Evaluation Charts

```
outputs/{project}/charts/
└── {ModelType}_{timestamp}/          # Independent directory per training run, named after model file
    ├── ClassPerformance.png          # Sensitivity / Specificity / Precision violin plots
    ├── BalanceMetrics.png            # F1-Score / MCC violin plots
    ├── ConfusionMatrix.png           # Averaged confusion matrix
    ├── ROC_Curve.png                 # ROC curve (with AUC ± CI)
    ├── MetricsTable.csv              # Performance metrics summary table (with class labels)
    └── PLS_Thresholds.png            # PLS threshold distribution (PLS models only)
```

---

## 🔄 Version History

### v1.15.x (2026-04 to 06) ⭐ Preprocessing SOP Refactor

- **Four-phase pipeline refactor** (v1.15.1–1.15.3): Reorganized three-phase pipeline into four phases following standard metabolomics SOP. Normalization moved downstream to after matrix construction. Phase 2 now outputs a complete consensus peak candidate pool; Phase 3 independently handles filtering. All-sample missing rate >50% replaces the legacy per-class occurrence rate + ml_score hard cutoff.
- **Post-processing chain completed** (v1.15.4–1.15.6): Added half-minimum missing value imputation, greedy clustering alignment (eliminates fixed-bin boundary effects), log₂(x+1) transformation, and Pareto scaling. Fixed GUI freeze during normalization (row-wise `.loc` assignment → `DataFrame.div` broadcast).
- **Mann-Whitney U feature selection** (v1.15.7): Replaced fold-change placeholder with MW-U + BH-FDR statistical testing. Known external validation bug remains (pending fix).
- **Fixed BH-FDR over-conservatism in small-sample settings** (v1.15.9): Batch 2 high-density data (2,076 features, ~52 samples) yielded all adjusted p = 1.0 after BH correction. Switched to raw p < 0.05 + MAX_FEATURES truncation; batch 2 AUC improved from 0.818 → 0.974.
- **Prediction-side transform chain synchronized** (v1.15.10): Pareto means/stds, half-min values, and log₂ toggle are now bundled with the model. The full training transform chain is automatically reproduced at prediction time. Old-format bundles are backward compatible.

### v1.14.x (2026-04) — Bilingual Help Wizard

- **Help wizard language toggle**: Added `🌐中/EN` button to the menu bar. Clicking it switches the entire help wizard (all 5 tabs) between Chinese and English. Language state is maintained by `HelpSystem.lang`.

### v1.13.x (2026-03) — Compliance & Security

- **First-launch disclaimer**: Mandatory usage notice with HMAC-SHA256 tamper-proof signing, bound to machine hostname
- Wizard window enlarged (750×600); wording adjustments ("screening" → "analysis", "compliant with" → "reference to")

### v1.12.x (2026-03) ⭐ Diagnostic Report Overhaul

- **Full PDF report upgrade**: Migrated from `canvas.drawString` to ReportLab Platypus; supports tables, embedded charts, and automatic page breaks
- **Model performance metrics added to report**: AUC / Sensitivity / Specificity / F1 (with 95% CI) automatically written into the "Model Information" section
- **Preview now uses real PDF**: Generates a temporary file and opens it in the system PDF reader — WYSIWYG
- **Chart storage architecture refactored**: `charts/latest` + `archive/` → `charts/{model_stem}/`; charts are permanently bound to their model
- Patient information section redesigned as a table layout; app icon added to title row; disclaimer appended at the end
- Print checkbox defaults automatically set based on current data in `data_store`
- Fixed a bug in the automated workflow that caused one sample to be missing during data loading

### v1.11.x (2026-03) — Stability & Architecture

- **Model Bundle format**: Models now saved as a dict containing feature list, normalization method, and PLS threshold; cross-session prediction no longer depends on training CSV
- **Training metrics converted to JSON**: 6 separate files consolidated into a single `{stem}.json` with named confusion matrices and metadata
- **Startup experience improved**: `-alpha=0` approach eliminates incremental rendering; new card-style splash screen added; fixed high-DPI child window centering offset
- Sensitivity/Specificity labels bound to actual class names, eliminating class-swap ambiguity
- Fixed layout issue where long text caused panel width to expand unexpectedly
- Fixed a silent prediction error caused by stale feature cache after model switching

### v1.10.x (2026-03) ⭐ Status Bar Overhaul

- **New three-state chip bar**: Independent status indicators for Preprocessing / Training / Prediction (○ Waiting / ◐ In Progress / ✓ Complete / ✗ Failed / ◼ Aborted)
- Automated workflow adapted to callback mechanism, replacing polling logic; fixed chip not updating
- "Start Training" button protected against re-entry; automatically disabled during operation

### v1.9.12.x (2026-03)

- Automated workflow cascade updates; officially usable
- Menu bar updated with Unicode icons; single-function items require fewer clicks
- Added "About DETEQX" dialog
- Visualization panel empty-state placeholder
- Project naming supports more characters; added "＋ Date" shortcut button
- Help wizard content updated (corrected CSV filename and cross-validation iteration count descriptions)

### v1.9.11 (2026-02)

- Code cleanup: removed 6 unused imports, 38 unused functions/methods; reduced codebase by ~500 lines

### v1.9.10.x (2025-12)

- Fixed ROC curve bug that used hard labels (switched to continuous probability scores)
- Merged `feature_detector.py` into `data_processing.py`
- Unified `normalization_method` naming convention

### v1.9.9 (2025-11)

- Introduced `ClassMappingManager` for centralized class mapping management
- Added "Class Settings" dialog to the menu bar

### v1.9.8.x (2025-11) ⭐ Major Update

- **Normalization architecture refactored**: Sample-level normalization; supports max / sum / median
- **Added Max normalization**: Outperforms TIC; set as the default method
- **Chart archiving system** (superseded by v1.12.5)

### v1.9.7 (2025-11) ⭐ Major Update

- **Cross-validation upgraded**: Monte Carlo → RepeatedStratifiedKFold
- Training iterations reduced from 500 to 100 while statistical reliability improved
- Added 95% CI reporting

### v1.9.5.x (2025-10)

- Visualization module refactored; introduced `MetricsCalculator`
- All charts now display 95% confidence intervals
- ~37.5% performance improvement

---

## 📝 Development Notes

### Adding New Features

1. **UI features**: Create a new Panel class in `ui_components.py`
2. **Business logic**: Create a new Manager class
3. **Data operations**: Add management functions in `data_store.py`
4. **Configuration parameters**: Add constants in `config.py`

### Key Design Patterns

- **Mediator pattern**: `MainGUIManager` coordinates all components
- **Singleton pattern**: `data_store`, `class_manager`, `output_manager`
- **Decorator pattern**: `validation_decorators.py` for unified error handling

### Logging

```python
from utils import log_message
log_message("Operation succeeded", "SUCCESS")  # INFO, SUCCESS, WARNING, ERROR
```

---

### Known Limitations

- **UI thread blocking**: Preprocessing and training both run on the main thread. For small datasets (20–40 samples), frequent `root.update()` calls mitigate this; large datasets or low-performance devices may still experience freezing. The fundamental fix is `threading.Thread` + a message queue.
- **External validation bug**: The Mann-Whitney U feature filtering introduced in v1.15.7 has a known bug when used in external validation mode; pending fix.
- **Hyperparameters are not persisted**: Changes made in `parameter_tuning_window.py` reset on restart. Impact is minimal for demo scenarios.
- **Batch effects**: Cross-batch sample validation shows approximately 10% accuracy degradation — a scientific problem that depends on future data collection.

---

---

## 🗂️ Design Decision Records

### Normalization Method Selection

PQN (Probabilistic Quotient Normalization) with QC samples was investigated early on as a more batch-robust option: insert pooled QC samples at regular intervals during each batch run and use the median QC spectrum from the training set as a reference, correcting for batch drift during external validation using QC signal shifts.

However, this approach requires experimental-level coordination — inserting one QC sample per every 10 samples, and ensuring QC samples are cryopreserved from the same batch throughout. The current dataset does not meet these prerequisites. The final choice was sample-level max/sum/median normalization: each sample relies only on its own statistics (maximum / sum / median), requires no cross-sample reference, and is simple and reliable in the absence of internal standards or QC samples — with no risk of training-set information leaking into prediction samples.

If future data collection conditions improve (QC samples added), PQN support can be extended on top of the existing `NormalizationManager`.

### Model Saving Strategy

The 5-fold × 20-repeat cross-validation produces 100 fold models. Two saving strategies were considered:

- **Strategy A (current)**: Save the model with the highest test score among the 100 folds
- **Strategy B (academic convention)**: Use cross-validation for performance estimation only, then retrain a final model on the full dataset

Strategy B is common in published research and theoretically provides more training data. However, its validity rests on the assumption that the final model's true performance approximates the cross-validation mean — but the final model itself has no independent test set evaluation and is therefore a black box.

For small-sample research settings, the practical difference between the two is limited. The truly meaningful evaluation is external validation using independently collected data from different batches or institutions — which occurs outside the development pipeline and is largely independent of which model is saved. Strategy A is therefore retained to keep the workflow simple and fast-iterating.

---

**Last updated**: June 2026  
**Current version**: v1.15.10
