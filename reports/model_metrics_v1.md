# Model metrics

Train: applications started 2022–2024. Test: started 2025, excluding sites that also appear in training. Everything (fill values, scaling, tuning, calibration, thresholds) is fitted on training years only, with cross-validation grouped by site. Missingness is not used as a feature.

Brier score: mean squared error of the probabilities (lower is better). PR-AUC: area under the precision–recall curve (compare with the positive rate). ROC-AUC 95% CI from 500 bootstrap resamples of the test set.

## A. P(approved), withdrawn = not approved

Train 6,442 rows (positive rate 47.4%); test 1,065 rows (positive rate 47.0%); 259 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.570 | 0.551 | 0.465 | 0.583 | 0.663 | 0.613 (0.580–0.644) | 0.574 | 0.239 |
| Logistic regression | 0.602 | 0.598 | 0.467 | 0.604 | 0.722 | 0.643 (0.609–0.674) | 0.615 | 0.233 |
| XGBoost (calibrated) | 0.587 | 0.599 | 0.369 | 0.582 | 0.780 | 0.646 (0.614–0.675) | 0.595 | 0.233 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.514 | 0.491 | 0.930 | 0.698 | 0.144 | 0.613 (0.580–0.644) | 0.574 | 0.239 |
| Logistic regression | 0.552 | 0.513 | 0.914 | 0.751 | 0.230 | 0.643 (0.609–0.674) | 0.615 | 0.233 |
| XGBoost (calibrated) | 0.581 | 0.533 | 0.886 | 0.754 | 0.310 | 0.646 (0.614–0.675) | 0.595 | 0.233 |

**1-9 homes** (test n = 1025, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.579 | 0.549 | 0.475 | 0.598 | 0.667 | 0.613 (0.580–0.647) | 0.567 | 0.238 |
| Logistic regression | 0.599 | 0.584 | 0.449 | 0.607 | 0.727 | 0.636 (0.601–0.670) | 0.593 | 0.233 |
| XGBoost (calibrated) | 0.584 | 0.582 | 0.347 | 0.585 | 0.787 | 0.637 (0.606–0.673) | 0.568 | 0.234 |

**10+ homes** (test n = 40, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.350 | 0.600 | 0.310 | 0.200 | 0.455 | 0.461 (0.225–0.700) | 0.718 | 0.257 |
| Logistic regression | 0.675 | 0.786 | 0.759 | 0.417 | 0.455 | 0.655 (0.447–0.836) | 0.841 | 0.213 |
| XGBoost (calibrated) | 0.650 | 0.778 | 0.724 | 0.385 | 0.455 | 0.704 (0.515–0.878) | 0.851 | 0.201 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 216}.

Leakage probe: a model using only *which fields are missing* scores ROC-AUC **0.521** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_referable` | +0.135 |
| `log_density` | -0.130 |
| `social_rent_pct_major` | +0.130 |
| `avg_home_size_m2` | +0.127 |
| `scheme_hmo` | -0.107 |
| `affordable_pct_major` | +0.106 |
| `log_homes_lost` | +0.096 |
| `in_article4_area` | -0.068 |
| `has_demolition` | +0.064 |
| `has_basement` | -0.060 |
| `has_commercial` | +0.057 |
| `log_nonresi` | -0.056 |

## A2. P(approved | decided), withdrawn excluded

Train 5,857 rows (positive rate 52.2%); test 993 rows (positive rate 51.2%); 237 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.584 | 0.593 | 0.598 | 0.575 | 0.569 | 0.631 (0.596–0.665) | 0.631 | 0.236 |
| Logistic regression | 0.594 | 0.609 | 0.579 | 0.580 | 0.610 | 0.662 (0.627–0.698) | 0.674 | 0.228 |
| XGBoost (calibrated) | 0.599 | 0.623 | 0.549 | 0.580 | 0.652 | 0.670 (0.638–0.705) | 0.659 | 0.227 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.568 | 0.548 | 0.892 | 0.669 | 0.229 | 0.631 (0.596–0.665) | 0.631 | 0.236 |
| Logistic regression | 0.599 | 0.570 | 0.878 | 0.706 | 0.307 | 0.662 (0.627–0.698) | 0.674 | 0.228 |
| XGBoost (calibrated) | 0.607 | 0.572 | 0.919 | 0.768 | 0.280 | 0.670 (0.638–0.705) | 0.659 | 0.227 |

**1-9 homes** (test n = 956, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.576 | 0.577 | 0.580 | 0.576 | 0.572 | 0.630 (0.591–0.664) | 0.625 | 0.236 |
| Logistic regression | 0.589 | 0.595 | 0.562 | 0.583 | 0.616 | 0.656 (0.620–0.689) | 0.655 | 0.230 |
| XGBoost (calibrated) | 0.592 | 0.607 | 0.528 | 0.581 | 0.656 | 0.662 (0.627–0.696) | 0.633 | 0.229 |

**10+ homes** (test n = 37, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.784 | 0.839 | 0.897 | 0.500 | 0.375 | 0.448 (0.168–0.725) | 0.756 | 0.234 |
| Logistic regression | 0.730 | 0.806 | 0.862 | 0.333 | 0.250 | 0.659 (0.432–0.853) | 0.873 | 0.185 |
| XGBoost (calibrated) | 0.784 | 0.839 | 0.897 | 0.500 | 0.375 | 0.672 (0.454–0.859) | 0.873 | 0.172 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 260}.

Leakage probe: a model using only *which fields are missing* scores ROC-AUC **0.513** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_referable` | +0.156 |
| `log_density` | -0.153 |
| `social_rent_pct_major` | +0.132 |
| `avg_home_size_m2` | +0.126 |
| `scheme_hmo` | -0.117 |
| `affordable_pct_major` | +0.111 |
| `log_homes_lost` | +0.088 |
| `in_article4_area` | -0.079 |
| `log_homes_net` | +0.076 |
| `has_commercial` | +0.065 |
| `in_town_centre` | +0.064 |
| `is_major` | +0.062 |

## B. P(S106 | approved)

Train 3,055 rows (positive rate 13.1%); test 606 rows (positive rate 11.7%); 53 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.903 | 0.875 | 0.197 | 0.322 | 0.910 (0.874–0.939) | 0.554 | 0.070 |
| Logistic regression | 0.919 | 0.739 | 0.479 | 0.581 | 0.946 (0.923–0.964) | 0.690 | 0.057 |
| XGBoost (calibrated) | 0.906 | 0.659 | 0.408 | 0.504 | 0.874 (0.818–0.918) | 0.580 | 0.070 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.832 | 0.403 | 0.901 | 0.557 | 0.910 (0.874–0.939) | 0.554 | 0.070 |
| Logistic regression | 0.899 | 0.551 | 0.761 | 0.639 | 0.946 (0.923–0.964) | 0.690 | 0.057 |
| XGBoost (calibrated) | 0.899 | 0.571 | 0.563 | 0.567 | 0.874 (0.818–0.918) | 0.580 | 0.070 |

**1-9 homes** (test n = 576, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.915 | 0.875 | 0.230 | 0.364 | 0.920 (0.885–0.950) | 0.568 | 0.061 |
| Logistic regression | 0.927 | 0.788 | 0.426 | 0.553 | 0.949 (0.927–0.969) | 0.709 | 0.052 |
| XGBoost (calibrated) | 0.911 | 0.639 | 0.377 | 0.474 | 0.876 (0.817–0.928) | 0.561 | 0.065 |

**10+ homes** (test n = 30, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.667 | 0.000 | 0.000 | 0.000 | 0.662 (0.466–0.849) | 0.453 | 0.236 |
| Logistic regression | 0.767 | 0.615 | 0.800 | 0.696 | 0.865 (0.702–0.970) | 0.785 | 0.169 |
| XGBoost (calibrated) | 0.800 | 0.750 | 0.600 | 0.667 | 0.775 (0.560–0.955) | 0.702 | 0.173 |

XGBoost settings chosen by grouped CV: {'max_depth': 2, 'min_child_weight': 5, 'n_rounds': 440}.

Leakage probe: a model using only *which fields are missing* scores ROC-AUC **0.485** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `log_homes_net` | +1.375 |
| `mayor_referable` | -0.618 |
| `is_outline` | -0.531 |
| `social_rent_pct_major` | +0.462 |
| `log_ptal` | +0.432 |
| `affordable_pct_major` | -0.288 |
| `is_major` | +0.251 |
| `imd_decile` | +0.202 |
| `dev_conversion` | -0.142 |
| `in_opportunity_area` | -0.133 |
| `has_commercial` | +0.116 |
| `dev_change_of_use` | +0.108 |

