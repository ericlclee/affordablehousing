# Model metrics

Train: applications started 2022–2024. Test: started 2025, excluding sites that also appear in training. Everything (fill values, scaling, tuning, calibration, thresholds) is fitted on training years only, with cross-validation grouped by site. Missingness is not used as a feature.

Brier score: mean squared error of the probabilities (lower is better). PR-AUC: area under the precision–recall curve (compare with the positive rate). ROC-AUC 95% CI from 500 bootstrap resamples of the test set.

## A. P(approved), withdrawn = not approved

Train 12,303 rows (positive rate 47.8%); test 2,328 rows (positive rate 48.0%); 466 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.591 | 0.613 | 0.402 | 0.581 | 0.765 | 0.615 (0.592–0.637) | 0.584 | 0.240 |
| Logistic regression | 0.594 | 0.595 | 0.487 | 0.594 | 0.693 | 0.638 (0.614–0.659) | 0.614 | 0.235 |
| XGBoost (calibrated) | 0.595 | 0.594 | 0.496 | 0.596 | 0.687 | 0.652 (0.630–0.674) | 0.621 | 0.232 |
| XGBoost + description text (offline) | 0.620 | 0.620 | 0.542 | 0.621 | 0.693 | 0.673 (0.652–0.695) | 0.641 | 0.227 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.522 | 0.501 | 0.901 | 0.652 | 0.172 | 0.615 (0.592–0.637) | 0.584 | 0.240 |
| Logistic regression | 0.537 | 0.510 | 0.925 | 0.721 | 0.179 | 0.638 (0.614–0.659) | 0.614 | 0.235 |
| XGBoost (calibrated) | 0.578 | 0.538 | 0.869 | 0.718 | 0.310 | 0.652 (0.630–0.674) | 0.621 | 0.232 |
| XGBoost + description text (offline) | 0.594 | 0.550 | 0.852 | 0.723 | 0.355 | 0.673 (0.652–0.695) | 0.641 | 0.227 |

**1-9 homes** (test n = 2264, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.588 | 0.602 | 0.387 | 0.582 | 0.769 | 0.613 (0.590–0.637) | 0.578 | 0.240 |
| Logistic regression | 0.593 | 0.587 | 0.477 | 0.596 | 0.697 | 0.634 (0.612–0.659) | 0.601 | 0.236 |
| XGBoost (calibrated) | 0.592 | 0.585 | 0.482 | 0.597 | 0.691 | 0.647 (0.625–0.670) | 0.610 | 0.233 |
| XGBoost + description text (offline) | 0.617 | 0.612 | 0.531 | 0.622 | 0.696 | 0.670 (0.648–0.693) | 0.631 | 0.228 |

**10+ homes** (test n = 64, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.688 | 0.786 | 0.750 | 0.500 | 0.550 | 0.616 (0.477–0.785) | 0.744 | 0.241 |
| Logistic regression | 0.641 | 0.744 | 0.727 | 0.429 | 0.450 | 0.660 (0.517–0.790) | 0.818 | 0.214 |
| XGBoost (calibrated) | 0.703 | 0.766 | 0.818 | 0.529 | 0.450 | 0.660 (0.522–0.803) | 0.808 | 0.211 |
| XGBoost + description text (offline) | 0.719 | 0.783 | 0.818 | 0.556 | 0.500 | 0.668 (0.516–0.806) | 0.780 | 0.208 |

**labelled by Foundations** (test n = 1037, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.582 | 0.577 | 0.387 | 0.585 | 0.753 | 0.606 (0.572–0.639) | 0.555 | 0.241 |
| Logistic regression | 0.591 | 0.578 | 0.453 | 0.599 | 0.711 | 0.639 (0.609–0.673) | 0.599 | 0.235 |
| XGBoost (calibrated) | 0.575 | 0.553 | 0.455 | 0.588 | 0.679 | 0.636 (0.603–0.667) | 0.588 | 0.235 |
| XGBoost + description text (offline) | 0.603 | 0.586 | 0.499 | 0.613 | 0.693 | 0.650 (0.619–0.680) | 0.596 | 0.233 |

**labelled by PLD** (test n = 1291, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.597 | 0.641 | 0.413 | 0.577 | 0.776 | 0.621 (0.592–0.650) | 0.601 | 0.239 |
| Logistic regression | 0.596 | 0.606 | 0.512 | 0.589 | 0.678 | 0.638 (0.606–0.667) | 0.628 | 0.236 |
| XGBoost (calibrated) | 0.611 | 0.624 | 0.526 | 0.602 | 0.694 | 0.664 (0.635–0.694) | 0.650 | 0.229 |
| XGBoost + description text (offline) | 0.634 | 0.644 | 0.575 | 0.627 | 0.692 | 0.692 (0.665–0.719) | 0.678 | 0.222 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 363}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.506** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.154 |
| `log_density` | -0.121 |
| `affordable_pct_major` | +0.119 |
| `avg_home_size_m2` | +0.118 |
| `space_std_share_below` | -0.117 |
| `statutory_major` | -0.117 |
| `log_homes_lost` | +0.110 |
| `is_major` | +0.101 |
| `scheme_hmo` | -0.096 |
| `has_basement` | -0.086 |
| `in_article4_area` | -0.083 |
| `in_conservation_area` | +0.077 |

**XGBoost + description text (offline)** stacks a TF-IDF + logistic-regression score of `description_at_submission` onto the XGBoost features (out-of-fold on training years). The simulator has no description, so this model is not in the browser bundle.

- Refusal-leaning terms: `rear of`, `large`, `studio flat`, `flats retrospective`, `dwelling following`, `bed use`, `proposed`, `at rear`, `hmo`, `waste storage`, `parking refuse`, `public house`, `shop`, `flats part`, `provide studio`
- Approval-leaning terms: `plant`, `into bedroom`, `dwellings with`, `residential class`, `existing building`, `existing property`, `as`, `accommodation`, `gardens`, `summary`, `site and`, `to bed`, `part retrospective`, `internal`, `ancillary`

## A2. P(approved | decided), withdrawn excluded

Train 11,216 rows (positive rate 52.5%); test 2,185 rows (positive rate 51.9%); 421 test rows removed for site overlap.

**Threshold 0.5**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.605 | 0.626 | 0.592 | 0.585 | 0.619 | 0.636 (0.609–0.658) | 0.646 | 0.236 |
| Logistic regression | 0.620 | 0.634 | 0.633 | 0.605 | 0.606 | 0.660 (0.635–0.682) | 0.677 | 0.231 |
| XGBoost (calibrated) | 0.615 | 0.626 | 0.637 | 0.602 | 0.590 | 0.668 (0.647–0.689) | 0.673 | 0.228 |
| XGBoost + description text (offline) | 0.627 | 0.638 | 0.645 | 0.613 | 0.606 | 0.688 (0.666–0.708) | 0.695 | 0.223 |

**Threshold chosen to maximise F1 on training out-of-fold predictions**

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.556 | 0.543 | 0.901 | 0.634 | 0.184 | 0.636 (0.609–0.658) | 0.646 | 0.236 |
| Logistic regression | 0.554 | 0.541 | 0.932 | 0.668 | 0.147 | 0.660 (0.635–0.682) | 0.677 | 0.231 |
| XGBoost (calibrated) | 0.590 | 0.566 | 0.899 | 0.704 | 0.258 | 0.668 (0.647–0.689) | 0.673 | 0.228 |
| XGBoost + description text (offline) | 0.612 | 0.584 | 0.874 | 0.708 | 0.330 | 0.688 (0.666–0.708) | 0.695 | 0.223 |

**1-9 homes** (test n = 2125, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.601 | 0.618 | 0.583 | 0.586 | 0.621 | 0.634 (0.612–0.659) | 0.641 | 0.236 |
| Logistic regression | 0.617 | 0.627 | 0.624 | 0.607 | 0.610 | 0.657 (0.634–0.679) | 0.668 | 0.231 |
| XGBoost (calibrated) | 0.612 | 0.620 | 0.628 | 0.603 | 0.595 | 0.665 (0.643–0.685) | 0.662 | 0.229 |
| XGBoost + description text (offline) | 0.624 | 0.632 | 0.638 | 0.616 | 0.610 | 0.684 (0.665–0.703) | 0.686 | 0.224 |

**10+ homes** (test n = 60, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.733 | 0.818 | 0.818 | 0.500 | 0.500 | 0.603 (0.430–0.775) | 0.778 | 0.224 |
| Logistic regression | 0.717 | 0.787 | 0.841 | 0.462 | 0.375 | 0.666 (0.518–0.805) | 0.868 | 0.206 |
| XGBoost (calibrated) | 0.717 | 0.776 | 0.864 | 0.455 | 0.312 | 0.655 (0.494–0.800) | 0.849 | 0.201 |
| XGBoost + description text (offline) | 0.700 | 0.783 | 0.818 | 0.429 | 0.375 | 0.703 (0.556–0.838) | 0.881 | 0.197 |

**labelled by Foundations** (test n = 973, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.603 | 0.628 | 0.533 | 0.585 | 0.675 | 0.625 (0.593–0.658) | 0.610 | 0.238 |
| Logistic regression | 0.614 | 0.627 | 0.586 | 0.602 | 0.642 | 0.659 (0.628–0.691) | 0.662 | 0.231 |
| XGBoost (calibrated) | 0.599 | 0.603 | 0.613 | 0.595 | 0.585 | 0.654 (0.619–0.687) | 0.644 | 0.232 |
| XGBoost + description text (offline) | 0.603 | 0.609 | 0.604 | 0.597 | 0.602 | 0.670 (0.639–0.703) | 0.660 | 0.229 |

**labelled by PLD** (test n = 1212, threshold 0.5)

| Model | Accuracy | Precision (approved) | Recall (approved) | Precision (not approved) | Recall (not approved) | ROC-AUC (95% CI) | PR-AUC (approved) | Brier |
|---|---|---|---|---|---|---|---|---|
| Baseline (borough x size rate) | 0.606 | 0.625 | 0.637 | 0.585 | 0.572 | 0.646 (0.613–0.676) | 0.668 | 0.234 |
| Logistic regression | 0.625 | 0.639 | 0.669 | 0.609 | 0.577 | 0.659 (0.627–0.688) | 0.691 | 0.230 |
| XGBoost (calibrated) | 0.627 | 0.644 | 0.656 | 0.607 | 0.594 | 0.679 (0.644–0.708) | 0.698 | 0.225 |
| XGBoost + description text (offline) | 0.645 | 0.660 | 0.677 | 0.628 | 0.610 | 0.702 (0.668–0.731) | 0.724 | 0.218 |

XGBoost settings chosen by grouped CV: {'max_depth': 4, 'min_child_weight': 5, 'n_rounds': 401}.

Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC **0.496** on the test set (0.5 = no signal).

Largest logistic-regression coefficients (standardised; positive = raises the probability; borough effects omitted):

| Feature | Coefficient |
|---|---|
| `mayor_1a_over_150_homes` | +0.169 |
| `avg_home_size_m2` | +0.132 |
| `log_density` | -0.129 |
| `space_std_share_below` | -0.120 |
| `affordable_pct_major` | +0.119 |
| `log_homes_lost` | +0.111 |
| `scheme_hmo` | -0.101 |
| `statutory_major` | -0.099 |
| `is_major` | +0.098 |
| `has_basement` | -0.091 |
| `log_homes_net` | +0.090 |
| `brownfield_site_within_50m` | +0.090 |

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

## Change from v1 (Foundations-only, 7,766 rows)

| Task | Model | v1 ROC-AUC | v2 ROC-AUC | v1 Brier | v2 Brier | v1 test n | v2 test n |
|---|---|---|---|---|---|---|---|
| A | Baseline (borough x size rate) | 0.613 | 0.615 | 0.239 | 0.240 | 1065 | 2328 |
| A | Logistic regression | 0.643 | 0.638 | 0.233 | 0.235 | 1065 | 2328 |
| A | XGBoost (calibrated) | 0.646 | 0.652 | 0.233 | 0.232 | 1065 | 2328 |
| A | XGBoost + description text (offline) | – | 0.673 | – | 0.227 | – | 2328 |
| A2 | Baseline (borough x size rate) | 0.631 | 0.636 | 0.236 | 0.236 | 993 | 2185 |
| A2 | Logistic regression | 0.662 | 0.660 | 0.228 | 0.231 | 993 | 2185 |
| A2 | XGBoost (calibrated) | 0.670 | 0.668 | 0.227 | 0.228 | 993 | 2185 |
| A2 | XGBoost + description text (offline) | – | 0.688 | – | 0.223 | – | 2185 |
| B | Baseline (borough x size rate) | 0.910 | 0.910 | 0.070 | 0.070 | 606 | 604 |
| B | Logistic regression | 0.946 | 0.945 | 0.057 | 0.058 | 606 | 604 |
| B | XGBoost (calibrated) | 0.874 | 0.873 | 0.070 | 0.071 | 606 | 604 |

