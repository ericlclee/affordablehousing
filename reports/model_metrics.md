# Model metrics

Train: applications started 2022–2024. Test: started 2025, excluding sites that also appear in training. Everything (fill values, scaling, tuning, calibration, thresholds) is fitted on training years only, with cross-validation grouped by site. Missingness is not used as a feature.

Brier score: mean squared error of the probabilities (lower is better). PR-AUC: area under the precision–recall curve (compare with the positive rate). ROC-AUC 95% CI from 500 bootstrap resamples of the test set.

## A. P(approved), withdrawn = not approved

Train 12,303 rows (positive rate 47.8%); test 2,328 rows (positive rate 48.0%); 466 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.591 | 0.613 | 0.402 | 0.581 | 0.765 | 0.615 (0.592–0.637) | 0.584 | 0.240 |
| Logistic regression | 0.596 | 0.597 | 0.489 | 0.596 | 0.695 | 0.637 (0.613–0.658) | 0.615 | 0.236 |
| XGBoost (calibrated) | 0.604 | 0.606 | 0.502 | 0.603 | 0.699 | 0.655 (0.634–0.674) | 0.623 | 0.231 |
| XGBoost + description text (offline) | 0.622 | 0.622 | 0.545 | 0.623 | 0.694 | 0.674 (0.654–0.696) | 0.645 | 0.227 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.522 | 0.501 | 0.901 | 0.652 | 0.172 | 0.615 (0.592–0.637) | 0.584 | 0.240 |
| Logistic regression | 0.531 | 0.506 | 0.932 | 0.719 | 0.160 | 0.637 (0.613–0.658) | 0.615 | 0.236 |
| XGBoost (calibrated) | 0.583 | 0.542 | 0.847 | 0.706 | 0.339 | 0.655 (0.634–0.674) | 0.623 | 0.231 |
| XGBoost + description text (offline) | 0.598 | 0.553 | 0.853 | 0.728 | 0.362 | 0.674 (0.654–0.696) | 0.645 | 0.227 |

**1-9 homes** (test n = 2264, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.588 | 0.602 | 0.387 | 0.582 | 0.769 | 0.613 (0.590–0.637) | 0.578 | 0.240 |
| Logistic regression | 0.595 | 0.590 | 0.480 | 0.599 | 0.699 | 0.632 (0.610–0.656) | 0.600 | 0.236 |
| XGBoost (calibrated) | 0.602 | 0.598 | 0.490 | 0.604 | 0.703 | 0.650 (0.627–0.673) | 0.613 | 0.232 |
| XGBoost + description text (offline) | 0.619 | 0.614 | 0.533 | 0.623 | 0.697 | 0.671 (0.648–0.694) | 0.633 | 0.227 |

**10+ homes** (test n = 64, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.688 | 0.786 | 0.750 | 0.500 | 0.550 | 0.616 (0.477–0.785) | 0.744 | 0.241 |
| Logistic regression | 0.625 | 0.738 | 0.705 | 0.409 | 0.450 | 0.674 (0.527–0.805) | 0.822 | 0.210 |
| XGBoost (calibrated) | 0.703 | 0.778 | 0.795 | 0.526 | 0.500 | 0.676 (0.525–0.828) | 0.788 | 0.206 |
| XGBoost + description text (offline) | 0.734 | 0.787 | 0.841 | 0.588 | 0.500 | 0.678 (0.528–0.810) | 0.806 | 0.203 |

**labelled by Foundations** (test n = 1037, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.582 | 0.577 | 0.387 | 0.585 | 0.753 | 0.606 (0.572–0.639) | 0.555 | 0.241 |
| Logistic regression | 0.590 | 0.576 | 0.455 | 0.598 | 0.708 | 0.635 (0.604–0.668) | 0.598 | 0.235 |
| XGBoost (calibrated) | 0.590 | 0.574 | 0.466 | 0.600 | 0.699 | 0.638 (0.606–0.668) | 0.582 | 0.235 |
| XGBoost + description text (offline) | 0.606 | 0.588 | 0.511 | 0.618 | 0.688 | 0.653 (0.622–0.684) | 0.602 | 0.232 |

**labelled by PLD** (test n = 1291, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.597 | 0.641 | 0.413 | 0.577 | 0.776 | 0.621 (0.592–0.650) | 0.601 | 0.239 |
| Logistic regression | 0.601 | 0.612 | 0.515 | 0.593 | 0.684 | 0.637 (0.606–0.666) | 0.629 | 0.236 |
| XGBoost (calibrated) | 0.616 | 0.630 | 0.529 | 0.606 | 0.700 | 0.668 (0.637–0.697) | 0.658 | 0.228 |
| XGBoost + description text (offline) | 0.636 | 0.648 | 0.570 | 0.627 | 0.700 | 0.692 (0.664–0.721) | 0.680 | 0.222 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 10, 'n_rounds': 433}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.506** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.149 |
| `statutory_major` | -0.128 |
| `space_std_share_below` | -0.122 |
| `affordable_pct_major` | +0.119 |
| `log_homes_lost` | +0.115 |
| `avg_home_size_m2` | +0.104 |
| `log_density` | -0.100 |
| `bf_multiple_houses` | +0.087 |
| `has_basement` | -0.083 |
| `in_article4_area` | -0.083 |
| `brownfield_site_within_50m` | +0.079 |
| `in_conservation_area` | +0.078 |

**XGBoost + description text (offline)** stacks a TF-IDF + logistic-regression score of `description_at_submission` onto the XGBoost features (out-of-fold on training years). The simulator has no description, so this model is not in the browser bundle.

- Refusal-leaning terms: `rear of`, `large`, `studio flat`, `flats retrospective`, `dwelling following`, `bed use`, `proposed`, `at rear`, `hmo`, `waste storage`, `parking refuse`, `public house`, `shop`, `flats part`, `provide studio`
- Approval-leaning terms: `plant`, `into bedroom`, `dwellings with`, `residential class`, `existing building`, `existing property`, `as`, `accommodation`, `gardens`, `summary`, `site and`, `to bed`, `part retrospective`, `internal`, `ancillary`

## A2. P(approved | decided), withdrawn excluded

Train 11,216 rows (positive rate 52.5%); test 2,185 rows (positive rate 51.9%); 421 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.605 | 0.626 | 0.592 | 0.585 | 0.619 | 0.636 (0.609–0.658) | 0.646 | 0.236 |
| Logistic regression | 0.615 | 0.627 | 0.634 | 0.601 | 0.594 | 0.657 (0.633–0.679) | 0.677 | 0.231 |
| XGBoost (calibrated) | 0.618 | 0.630 | 0.638 | 0.605 | 0.597 | 0.673 (0.651–0.694) | 0.677 | 0.227 |
| XGBoost + description text (offline) | 0.627 | 0.638 | 0.650 | 0.615 | 0.604 | 0.686 (0.664–0.708) | 0.694 | 0.223 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.556 | 0.543 | 0.901 | 0.634 | 0.184 | 0.636 (0.609–0.658) | 0.646 | 0.236 |
| Logistic regression | 0.554 | 0.540 | 0.936 | 0.676 | 0.143 | 0.657 (0.633–0.679) | 0.677 | 0.231 |
| XGBoost (calibrated) | 0.593 | 0.568 | 0.898 | 0.707 | 0.263 | 0.673 (0.651–0.694) | 0.677 | 0.227 |
| XGBoost + description text (offline) | 0.615 | 0.585 | 0.881 | 0.719 | 0.328 | 0.686 (0.664–0.708) | 0.694 | 0.223 |

**1-9 homes** (test n = 2125, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.601 | 0.618 | 0.583 | 0.586 | 0.621 | 0.634 (0.612–0.659) | 0.641 | 0.236 |
| Logistic regression | 0.613 | 0.621 | 0.626 | 0.604 | 0.598 | 0.654 (0.633–0.677) | 0.666 | 0.232 |
| XGBoost (calibrated) | 0.616 | 0.624 | 0.628 | 0.606 | 0.602 | 0.670 (0.648–0.691) | 0.666 | 0.228 |
| XGBoost + description text (offline) | 0.625 | 0.632 | 0.641 | 0.617 | 0.608 | 0.682 (0.662–0.700) | 0.683 | 0.225 |

**10+ homes** (test n = 60, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.733 | 0.818 | 0.818 | 0.500 | 0.500 | 0.603 (0.430–0.775) | 0.778 | 0.224 |
| Logistic regression | 0.683 | 0.766 | 0.818 | 0.385 | 0.312 | 0.666 (0.526–0.804) | 0.872 | 0.203 |
| XGBoost (calibrated) | 0.717 | 0.765 | 0.886 | 0.444 | 0.250 | 0.655 (0.487–0.794) | 0.851 | 0.198 |
| XGBoost + description text (offline) | 0.717 | 0.776 | 0.864 | 0.455 | 0.312 | 0.700 (0.558–0.834) | 0.872 | 0.186 |

**labelled by Foundations** (test n = 973, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.603 | 0.628 | 0.533 | 0.585 | 0.675 | 0.625 (0.593–0.658) | 0.610 | 0.238 |
| Logistic regression | 0.610 | 0.622 | 0.590 | 0.600 | 0.631 | 0.656 (0.625–0.689) | 0.663 | 0.231 |
| XGBoost (calibrated) | 0.602 | 0.610 | 0.598 | 0.595 | 0.606 | 0.656 (0.623–0.688) | 0.646 | 0.233 |
| XGBoost + description text (offline) | 0.610 | 0.618 | 0.606 | 0.603 | 0.615 | 0.667 (0.634–0.697) | 0.655 | 0.230 |

**labelled by PLD** (test n = 1212, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.606 | 0.625 | 0.637 | 0.585 | 0.572 | 0.646 (0.613–0.676) | 0.668 | 0.234 |
| Logistic regression | 0.618 | 0.631 | 0.667 | 0.602 | 0.563 | 0.658 (0.625–0.685) | 0.690 | 0.231 |
| XGBoost (calibrated) | 0.631 | 0.646 | 0.669 | 0.614 | 0.589 | 0.688 (0.656–0.717) | 0.705 | 0.223 |
| XGBoost + description text (offline) | 0.641 | 0.653 | 0.683 | 0.626 | 0.594 | 0.701 (0.668–0.730) | 0.725 | 0.218 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 389}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.496** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.168 |
| `space_std_share_below` | -0.125 |
| `affordable_pct_major` | +0.120 |
| `log_density` | -0.117 |
| `log_homes_lost` | +0.117 |
| `avg_home_size_m2` | +0.114 |
| `statutory_major` | -0.110 |
| `log_homes_net` | +0.102 |
| `bf_multiple_houses` | +0.098 |
| `brownfield_site_within_50m` | +0.093 |
| `has_basement` | -0.087 |
| `in_article4_area` | -0.082 |

**XGBoost + description text (offline)** stacks a TF-IDF + logistic-regression score of `description_at_submission` onto the XGBoost features (out-of-fold on training years). The simulator has no description, so this model is not in the browser bundle.

- Refusal-leaning terms: `rear of`, `studio flat`, `large`, `hmo`, `extension to`, `at rear`, `dwelling following`, `flats retrospective`, `waste storage`, `provide studio`, `proposed conversion`, `with parking`, `parking refuse`, `storage building`, `public house`
- Approval-leaning terms: `plant`, `residential class`, `as`, `gardens`, `accommodation`, `dwellings with`, `existing building`, `into bedroom`, `summary`, `existing property`, `site and`, `replacement`, `f2`, `ancillary`, `part retrospective`

## B. P(S106 | approved)

Train 3,023 rows (positive rate 13.2%); test 604 rows (positive rate 11.8%); 48 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.902 | 0.875 | 0.197 | 0.322 | 0.910 (0.878–0.942) | 0.555 | 0.070 |
| Logistic regression | 0.916 | 0.708 | 0.479 | 0.571 | 0.945 (0.924–0.963) | 0.687 | 0.058 |
| XGBoost (calibrated) | 0.904 | 0.623 | 0.465 | 0.532 | 0.873 (0.826–0.920) | 0.574 | 0.071 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.831 | 0.403 | 0.901 | 0.557 | 0.910 (0.878–0.942) | 0.555 | 0.070 |
| Logistic regression | 0.916 | 0.632 | 0.676 | 0.653 | 0.945 (0.924–0.963) | 0.687 | 0.058 |
| XGBoost (calibrated) | 0.897 | 0.563 | 0.563 | 0.563 | 0.873 (0.826–0.920) | 0.574 | 0.071 |

**1-9 homes** (test n = 575, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.915 | 0.875 | 0.230 | 0.364 | 0.920 (0.888–0.949) | 0.568 | 0.061 |
| Logistic regression | 0.927 | 0.788 | 0.426 | 0.553 | 0.949 (0.925–0.967) | 0.708 | 0.051 |
| XGBoost (calibrated) | 0.910 | 0.600 | 0.443 | 0.509 | 0.873 (0.821–0.922) | 0.558 | 0.065 |

**10+ homes** (test n = 29, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.655 | 0.000 | 0.000 | 0.000 | 0.655 (0.438–0.844) | 0.458 | 0.243 |
| Logistic regression | 0.690 | 0.533 | 0.800 | 0.640 | 0.853 (0.701–0.975) | 0.786 | 0.195 |
| XGBoost (calibrated) | 0.793 | 0.750 | 0.600 | 0.667 | 0.763 (0.572–0.938) | 0.679 | 0.177 |

**labelled by Foundations** (test n = 604, threshold 0.5)

| Model | Accuracy | Precision (S106) | Recall (S106) | F1 (S106) | ROC-AUC (95% CI) | PR-AUC (S106) | Brier |
|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.902 | 0.875 | 0.197 | 0.322 | 0.910 (0.878–0.942) | 0.555 | 0.070 |
| Logistic regression | 0.916 | 0.708 | 0.479 | 0.571 | 0.945 (0.924–0.963) | 0.687 | 0.058 |
| XGBoost (calibrated) | 0.904 | 0.623 | 0.465 | 0.532 | 0.873 (0.826–0.920) | 0.574 | 0.071 |

XGBoost settings chosen by grouped CV: {'max_depth': 3, 'min_child_weight': 5, 'n_rounds': 274}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.486** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `log_homes_net` | +1.467 |
| `is_major` | +1.280 |
| `statutory_major` | -1.144 |
| `is_outline` | -0.610 |
| `mayor_1a_over_150_homes` | -0.557 |
| `log_ptal` | +0.409 |
| `social_rent_pct_major` | +0.405 |
| `affordable_pct_major` | -0.238 |
| `imd_decile` | +0.197 |
| `in_opportunity_area` | -0.169 |
| `dev_change_of_use` | +0.142 |
| `dev_conversion` | -0.125 |

## Stopping conditions (approval model, 2025 test set)

69 of 2,328 test applications (3.0%) get no probability: they are on a policy STOP site or outside the range of schemes the model was trained on. Reasons (a row can have several):

| Reason | Test applications |
|---|---|
| STOP: Green Belt | 36 |
| denser than 99.9% of schemes seen | 15 |
| smaller site than 99.5% of schemes seen | 10 |
| taller for its site size than 99% of schemes seen | 4 |
| more existing homes lost than 99.9% of schemes seen | 3 |
| more homes than 99.9% of schemes seen | 2 |
| STOP: Strategic Industrial Location | 1 |
| larger site than 99.9% of schemes seen | 1 |

Within range: n = 2259, ROC-AUC 0.659, Brier 0.230, approval rate 47.9%.

Guarded (for reference: what the model would have said): n = 69, ROC-AUC 0.510, Brier 0.264, approval rate 53.6%.

## Change from v1 (Foundations-only, 7,766 rows)

| Task | Model | v1 ROC-AUC | v2 ROC-AUC | v1 Brier | v2 Brier | v1 test n | v2 test n |
|---|---|---|---|---|---|---|---|
| A | Baseline (borough x size rate) | 0.613 | 0.615 | 0.239 | 0.240 | 1065 | 2328 |
| A | Logistic regression | 0.643 | 0.637 | 0.233 | 0.236 | 1065 | 2328 |
| A | XGBoost (calibrated) | 0.646 | 0.655 | 0.233 | 0.231 | 1065 | 2328 |
| A | XGBoost + description text (offline) | – | 0.674 | – | 0.227 | – | 2328 |
| A2 | Baseline (borough x size rate) | 0.631 | 0.636 | 0.236 | 0.236 | 993 | 2185 |
| A2 | Logistic regression | 0.662 | 0.657 | 0.228 | 0.231 | 993 | 2185 |
| A2 | XGBoost (calibrated) | 0.670 | 0.673 | 0.227 | 0.227 | 993 | 2185 |
| A2 | XGBoost + description text (offline) | – | 0.686 | – | 0.223 | – | 2185 |
| B | Baseline (borough x size rate) | 0.910 | 0.910 | 0.070 | 0.070 | 606 | 604 |
| B | Logistic regression | 0.946 | 0.945 | 0.057 | 0.058 | 606 | 604 |
| B | XGBoost (calibrated) | 0.874 | 0.873 | 0.070 | 0.071 | 606 | 604 |

