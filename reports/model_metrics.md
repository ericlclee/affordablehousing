# Model metrics

Train: applications started 2022–2024. Test: started 2025, excluding sites that also appear in training. Everything (fill values, scaling, tuning, calibration, thresholds) is fitted on training years only, with cross-validation grouped by site. Missingness is not used as a feature.

Brier score: mean squared error of the probabilities (lower is better). PR-AUC: area under the precision–recall curve (compare with the positive rate). ROC-AUC 95% CI from 500 bootstrap resamples of the test set.

## A. P(approved), withdrawn = not approved

Train 12,344 rows (positive rate 48.0%); test 2,333 rows (positive rate 48.1%); 472 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.590 | 0.613 | 0.402 | 0.580 | 0.764 | 0.616 (0.593–0.639) | 0.585 | 0.239 |
| Logistic regression | 0.592 | 0.594 | 0.483 | 0.591 | 0.693 | 0.638 (0.614–0.660) | 0.618 | 0.235 |
| XGBoost (calibrated) | 0.601 | 0.603 | 0.497 | 0.599 | 0.697 | 0.655 (0.631–0.675) | 0.627 | 0.231 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.523 | 0.502 | 0.901 | 0.652 | 0.172 | 0.616 (0.593–0.639) | 0.585 | 0.239 |
| Logistic regression | 0.538 | 0.511 | 0.923 | 0.715 | 0.180 | 0.638 (0.614–0.660) | 0.618 | 0.235 |
| XGBoost (calibrated) | 0.565 | 0.529 | 0.898 | 0.731 | 0.256 | 0.655 (0.631–0.675) | 0.627 | 0.231 |

**1-9 homes** (test n = 2267, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.588 | 0.603 | 0.387 | 0.581 | 0.769 | 0.613 (0.591–0.635) | 0.579 | 0.239 |
| Logistic regression | 0.590 | 0.585 | 0.472 | 0.593 | 0.697 | 0.633 (0.611–0.656) | 0.602 | 0.236 |
| XGBoost (calibrated) | 0.597 | 0.593 | 0.482 | 0.599 | 0.701 | 0.649 (0.628–0.670) | 0.616 | 0.232 |

**10+ homes** (test n = 66, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.682 | 0.778 | 0.761 | 0.476 | 0.500 | 0.622 (0.478–0.777) | 0.760 | 0.239 |
| Logistic regression | 0.652 | 0.756 | 0.739 | 0.429 | 0.450 | 0.673 (0.514–0.790) | 0.832 | 0.206 |
| XGBoost (calibrated) | 0.727 | 0.780 | 0.848 | 0.562 | 0.450 | 0.672 (0.512–0.807) | 0.803 | 0.202 |

**labelled by Foundations** (test n = 1039, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.582 | 0.578 | 0.390 | 0.584 | 0.751 | 0.608 (0.573–0.640) | 0.557 | 0.241 |
| Logistic regression | 0.588 | 0.576 | 0.445 | 0.595 | 0.713 | 0.639 (0.603–0.675) | 0.604 | 0.234 |
| XGBoost (calibrated) | 0.578 | 0.561 | 0.443 | 0.588 | 0.697 | 0.639 (0.603–0.677) | 0.592 | 0.235 |

**labelled by PLD** (test n = 1294, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.597 | 0.641 | 0.412 | 0.576 | 0.776 | 0.621 (0.591–0.648) | 0.602 | 0.239 |
| Logistic regression | 0.595 | 0.606 | 0.511 | 0.587 | 0.677 | 0.638 (0.605–0.664) | 0.630 | 0.236 |
| XGBoost (calibrated) | 0.618 | 0.633 | 0.538 | 0.608 | 0.697 | 0.667 (0.637–0.694) | 0.657 | 0.229 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 340}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.505** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.165 |
| `affordable_pct_major` | +0.118 |
| `space_std_share_below` | -0.116 |
| `avg_home_size_m2` | +0.116 |
| `statutory_major` | -0.115 |
| `log_homes_lost` | +0.112 |
| `log_density` | -0.111 |
| `is_major` | +0.103 |
| `scheme_hmo` | -0.095 |
| `has_basement` | -0.086 |
| `in_article4_area` | -0.084 |
| `brownfield_site_within_50m` | +0.078 |

## A2. P(approved | decided), withdrawn excluded

Train 11,252 rows (positive rate 52.6%); test 2,190 rows (positive rate 52.0%); 426 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.600 | 0.614 | 0.619 | 0.584 | 0.579 | 0.637 (0.614–0.659) | 0.647 | 0.235 |
| Logistic regression | 0.621 | 0.635 | 0.635 | 0.606 | 0.606 | 0.659 (0.636–0.682) | 0.679 | 0.230 |
| XGBoost (calibrated) | 0.613 | 0.626 | 0.632 | 0.598 | 0.592 | 0.667 (0.643–0.691) | 0.673 | 0.229 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.557 | 0.545 | 0.902 | 0.634 | 0.184 | 0.637 (0.614–0.659) | 0.647 | 0.235 |
| Logistic regression | 0.548 | 0.537 | 0.941 | 0.660 | 0.124 | 0.659 (0.636–0.682) | 0.679 | 0.230 |
| XGBoost (calibrated) | 0.591 | 0.568 | 0.890 | 0.693 | 0.268 | 0.667 (0.643–0.691) | 0.673 | 0.229 |

**1-9 homes** (test n = 2128, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.596 | 0.607 | 0.605 | 0.585 | 0.587 | 0.635 (0.610–0.658) | 0.641 | 0.236 |
| Logistic regression | 0.618 | 0.628 | 0.625 | 0.607 | 0.610 | 0.656 (0.633–0.681) | 0.668 | 0.231 |
| XGBoost (calibrated) | 0.609 | 0.619 | 0.622 | 0.599 | 0.597 | 0.663 (0.639–0.684) | 0.660 | 0.230 |

**10+ homes** (test n = 62, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.710 | 0.741 | 0.935 | 0.250 | 0.062 | 0.599 (0.421–0.768) | 0.790 | 0.221 |
| Logistic regression | 0.726 | 0.784 | 0.870 | 0.455 | 0.312 | 0.682 (0.525–0.831) | 0.879 | 0.197 |
| XGBoost (calibrated) | 0.726 | 0.784 | 0.870 | 0.455 | 0.312 | 0.686 (0.520–0.841) | 0.879 | 0.194 |

**labelled by Foundations** (test n = 975, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.597 | 0.615 | 0.549 | 0.582 | 0.646 | 0.627 (0.589–0.660) | 0.612 | 0.238 |
| Logistic regression | 0.614 | 0.629 | 0.588 | 0.602 | 0.642 | 0.659 (0.624–0.689) | 0.665 | 0.231 |
| XGBoost (calibrated) | 0.597 | 0.604 | 0.598 | 0.590 | 0.596 | 0.656 (0.619–0.689) | 0.650 | 0.232 |

**labelled by PLD** (test n = 1215, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.602 | 0.613 | 0.672 | 0.586 | 0.523 | 0.646 (0.617–0.676) | 0.668 | 0.234 |
| Logistic regression | 0.626 | 0.640 | 0.672 | 0.609 | 0.575 | 0.659 (0.630–0.685) | 0.692 | 0.230 |
| XGBoost (calibrated) | 0.626 | 0.643 | 0.658 | 0.605 | 0.589 | 0.675 (0.646–0.703) | 0.692 | 0.226 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 327}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.497** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.176 |
| `avg_home_size_m2` | +0.129 |
| `log_density` | -0.124 |
| `affordable_pct_major` | +0.121 |
| `space_std_share_below` | -0.121 |
| `log_homes_lost` | +0.113 |
| `scheme_hmo` | -0.100 |
| `is_major` | +0.099 |
| `statutory_major` | -0.096 |
| `brownfield_site_within_50m` | +0.093 |
| `has_basement` | -0.091 |
| `log_homes_net` | +0.090 |

## B. P(S106 | approved)

Train 3,055 rows (positive rate 13.1%); test 606 rows (positive rate 11.7%); 53 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.903 | 0.875 | 0.197 | 0.322 | 0.910 (0.874–0.939) | 0.554 | 0.070 |
| Logistic regression | 0.919 | 0.739 | 0.479 | 0.581 | 0.946 (0.924–0.964) | 0.691 | 0.058 |
| XGBoost (calibrated) | 0.904 | 0.627 | 0.451 | 0.525 | 0.875 (0.821–0.918) | 0.593 | 0.070 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.832 | 0.403 | 0.901 | 0.557 | 0.910 (0.874–0.939) | 0.554 | 0.070 |
| Logistic regression | 0.901 | 0.556 | 0.775 | 0.647 | 0.946 (0.924–0.964) | 0.691 | 0.058 |
| XGBoost (calibrated) | 0.898 | 0.563 | 0.563 | 0.563 | 0.875 (0.821–0.918) | 0.593 | 0.070 |

**1-9 homes** (test n = 576, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.915 | 0.875 | 0.230 | 0.364 | 0.920 (0.885–0.950) | 0.568 | 0.061 |
| Logistic regression | 0.927 | 0.788 | 0.426 | 0.553 | 0.951 (0.929–0.970) | 0.712 | 0.051 |
| XGBoost (calibrated) | 0.911 | 0.619 | 0.426 | 0.505 | 0.878 (0.821–0.926) | 0.573 | 0.065 |

**10+ homes** (test n = 30, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.667 | 0.000 | 0.000 | 0.000 | 0.662 (0.466–0.849) | 0.453 | 0.236 |
| Logistic regression | 0.767 | 0.615 | 0.800 | 0.696 | 0.850 (0.684–0.962) | 0.770 | 0.185 |
| XGBoost (calibrated) | 0.767 | 0.667 | 0.600 | 0.632 | 0.775 (0.559–0.956) | 0.746 | 0.181 |

**labelled by Foundations** (test n = 606, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.903 | 0.875 | 0.197 | 0.322 | 0.910 (0.874–0.939) | 0.554 | 0.070 |
| Logistic regression | 0.919 | 0.739 | 0.479 | 0.581 | 0.946 (0.924–0.964) | 0.691 | 0.058 |
| XGBoost (calibrated) | 0.904 | 0.627 | 0.451 | 0.525 | 0.875 (0.821–0.918) | 0.593 | 0.070 |

XGBoost settings chosen by grouped CV: {'max_depth': 2, 'min_child_weight': 5, 'n_rounds': 466}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.485** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `log_homes_net` | +1.457 |
| `is_major` | +1.244 |
| `statutory_major` | -1.130 |
| `mayor_1a_over_150_homes` | -0.597 |
| `is_outline` | -0.532 |
| `social_rent_pct_major` | +0.517 |
| `log_ptal` | +0.412 |
| `affordable_pct_major` | -0.340 |
| `imd_decile` | +0.201 |
| `in_opportunity_area` | -0.170 |
| `dev_change_of_use` | +0.133 |
| `dev_conversion` | -0.124 |

## Change from v1 (Foundations-only, 7,766 rows)

| Task | Model | v1 ROC-AUC | v2 ROC-AUC | v1 Brier | v2 Brier | v1 test n | v2 test n |
|---|---|---|---|---|---|---|---|
| A | Baseline (borough x size rate) | 0.613 | 0.616 | 0.239 | 0.239 | 1065 | 2333 |
| A | Logistic regression | 0.643 | 0.638 | 0.233 | 0.235 | 1065 | 2333 |
| A | XGBoost (calibrated) | 0.646 | 0.655 | 0.233 | 0.231 | 1065 | 2333 |
| A2 | Baseline (borough x size rate) | 0.631 | 0.637 | 0.236 | 0.235 | 993 | 2190 |
| A2 | Logistic regression | 0.662 | 0.659 | 0.228 | 0.230 | 993 | 2190 |
| A2 | XGBoost (calibrated) | 0.670 | 0.667 | 0.227 | 0.229 | 993 | 2190 |
| B | Baseline (borough x size rate) | 0.910 | 0.910 | 0.070 | 0.070 | 606 | 606 |
| B | Logistic regression | 0.946 | 0.946 | 0.057 | 0.058 | 606 | 606 |
| B | XGBoost (calibrated) | 0.874 | 0.875 | 0.070 | 0.070 | 606 | 606 |

