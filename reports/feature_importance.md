# What drives the approval model

XGBoost approval model, 2025 test set (2,333 proposals, ROC-AUC 0.655). **ROC-AUC lost**: drop in ROC-AUC when the feature is shuffled (mean of 30, with 95% interval); **Effect**: change in mean predicted approval from a low to a high value (10th → 90th percentile of the model's input scale, or no → yes), everything else unchanged. Log-scale features (`log_*`) show log values. These are associations in historical decisions, not causal effects.

## Features with a real effect (interval above zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| Borough | 0.0860 (0.0703 to 0.1035) | 28% (Waltham Forest) to 69% (Haringey) for the same schemes |
| avg_home_size_m2 | 0.0126 (0.0075 to 0.0165) | 48.9 → 125: +7.3 pp |
| Unit mix (studio / 1b / 2b share) | 0.0069 (0.0024 to 0.0105) | studio -1.3 pp, 1b +1.2 pp, 2b +1.5 pp vs reference |
| log_homes_net | 0.0069 (0.0014 to 0.0113) | 0.693 → 2.08: -2.4 pp |
| Scheme type (HMO / student / co-living) | 0.0067 (0.0040 to 0.0094) | hmo -6.8 pp, student coliving +0.0 pp vs reference |
| space_std_share_below | 0.0061 (0.0026 to 0.0107) | 0 → 0.5: -3.4 pp |
| log_ptal | 0.0061 (0.0001 to 0.0101) | 1.59 → 3.4: -0.5 pp |
| log_site_area | 0.0061 (0.0025 to 0.0099) | 4.73 → 7.03: +6.5 pp |
| log_density | 0.0043 (0.0009 to 0.0091) | 3.01 → 5.25: -3.3 pp |
| has_demolition | 0.0012 (0.0004 to 0.0019) | no → yes: +0.9 pp |
| in_article4_area | 0.0010 (0.0006 to 0.0013) | no → yes: -0.5 pp |

## No clear effect (interval includes zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| log_homes_lost | 0.0033 (-0.0027 to 0.0074) | 0 → 0.693: +6.0 pp |
| affordable_pct_major | 0.0019 (-0.0003 to 0.0039) | 0 → 100: +18.4 pp (10+ home schemes) |
| has_basement | 0.0016 (-0.0009 to 0.0038) | no → yes: -4.8 pp |
| storeys | 0.0012 (-0.0000 to 0.0023) | 2 → 4: +0.8 pp |
| imd_decile | 0.0010 (-0.0009 to 0.0030) | 2 → 9: +1.4 pp |
| in_conservation_area | 0.0009 (-0.0013 to 0.0027) | no → yes: +2.6 pp |
| Development type | 0.0008 (-0.0002 to 0.0015) | change of use +0.2 pp, conversion -0.2 pp, extension +0.2 pp vs reference |
| in_opportunity_area | 0.0004 (-0.0002 to 0.0008) | no → yes: -0.4 pp |
| log_nonresi | 0.0003 (-0.0014 to 0.0020) | 0 → 4.3: -3.6 pp |
| has_commercial | 0.0003 (-0.0008 to 0.0013) | no → yes: +2.0 pp |
| has_roof_terrace | 0.0002 (-0.0005 to 0.0008) | no → yes: +2.3 pp |
| social_rent_pct_major | 0.0001 (-0.0004 to 0.0007) | 0 → 26.6: +2.4 pp (10+ home schemes) |
| Flood zone | 0.0000 (-0.0003 to 0.0003) | zone 2 +0.2 pp, zone 3 -0.4 pp vs reference |
| mayor_1c_height | 0.0000 (-0.0000 to 0.0000) | no → yes: -0.1 pp |
| mayor_1a_over_150_homes | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| is_major | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| in_green_belt | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| premium_amenity | -0.0000 (-0.0002 to 0.0002) | no → yes: +1.2 pp |
| has_communal_amenity | -0.0000 (-0.0001 to -0.0000) | no → yes: +0.0 pp |
| in_town_centre | -0.0001 (-0.0017 to 0.0014) | no → yes: +2.4 pp |
| brownfield_site_within_50m | -0.0002 (-0.0027 to 0.0023) | no → yes: +4.6 pp |
| statutory_major | -0.0003 (-0.0006 to 0.0000) | no → yes: -0.7 pp |
| is_outline | -0.0003 (-0.0010 to 0.0003) | no → yes: -2.1 pp |
| listed_building_within_25m | -0.0003 (-0.0011 to 0.0003) | no → yes: +2.3 pp |

