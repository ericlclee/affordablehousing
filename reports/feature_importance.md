# What drives the approval model

XGBoost approval model, 2025 test set (2,328 proposals, ROC-AUC 0.655). **ROC-AUC lost**: drop in ROC-AUC when the feature is shuffled (mean of 30, with 95% interval); **Effect**: change in mean predicted approval from a low to a high value (10th → 90th percentile of the model's input scale, or no → yes), everything else unchanged. Log-scale features (`log_*`) show log values. These are associations in historical decisions, not causal effects.

## Features with a real effect (interval above zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| Borough | 0.0850 (0.0692 to 0.0952) | 28% (Waltham Forest) to 68% (Haringey) for the same schemes |
| log_density | 0.0110 (0.0069 to 0.0146) | 3.01 → 5.25: -6.3 pp |
| avg_home_size_m2 | 0.0099 (0.0058 to 0.0157) | 48.8 → 125: +4.0 pp |
| Unit mix (studio / 1b / 2b share) | 0.0092 (0.0040 to 0.0133) | studio -0.0 pp, 1b +2.6 pp, 2b +1.8 pp vs reference |
| space_std_share_below | 0.0076 (0.0021 to 0.0133) | 0 → 0.5: -3.6 pp |
| log_homes_net | 0.0063 (0.0006 to 0.0111) | 0.693 → 2.08: -2.0 pp |
| log_ptal | 0.0048 (0.0014 to 0.0090) | 1.59 → 3.4: +0.2 pp |
| Scheme type (HMO / student / co-living) | 0.0047 (0.0027 to 0.0067) | hmo -4.8 pp, student coliving +0.0 pp vs reference |
| Build form (houses / flats / block…) | 0.0032 (0.0011 to 0.0062) | single house -0.3 pp, multiple houses +4.0 pp, single flat +1.4 pp, apartment block +0.4 pp, mixed -2.2 pp, hmo -1.7 pp, student coliving +0.0 pp vs reference |
| in_conservation_area | 0.0025 (0.0001 to 0.0043) | no → yes: +2.6 pp |
| affordable_pct_major | 0.0022 (0.0002 to 0.0040) | 0 → 100: +19.8 pp (10+ home schemes) |
| has_basement | 0.0020 (0.0000 to 0.0043) | no → yes: -5.9 pp |
| in_article4_area | 0.0009 (0.0002 to 0.0017) | no → yes: -0.7 pp |
| in_opportunity_area | 0.0007 (0.0002 to 0.0013) | no → yes: -0.1 pp |
| has_pub_loss | 0.0006 (0.0002 to 0.0008) | no → yes: -2.9 pp |
| Flood zone | 0.0005 (0.0000 to 0.0009) | zone 2 +0.2 pp, zone 3 -0.8 pp vs reference |

## No clear effect (interval includes zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| log_homes_lost | 0.0024 (-0.0037 to 0.0063) | 0 → 0.693: +5.7 pp |
| imd_decile | 0.0019 (-0.0008 to 0.0041) | 2 → 9: +0.9 pp |
| log_site_area | 0.0014 (-0.0034 to 0.0053) | 4.73 → 7.02: +3.6 pp |
| has_commercial | 0.0008 (-0.0006 to 0.0021) | no → yes: +2.5 pp |
| Development type | 0.0006 (-0.0006 to 0.0015) | change of use +0.3 pp, conversion -0.5 pp, extension +0.6 pp vs reference |
| has_roof_terrace | 0.0005 (-0.0006 to 0.0014) | no → yes: +2.2 pp |
| log_nonresi | 0.0002 (-0.0013 to 0.0019) | 0 → 4.31: -3.5 pp |
| storeys | 0.0002 (-0.0013 to 0.0014) | 2 → 4: +0.5 pp |
| in_town_centre | 0.0001 (-0.0012 to 0.0014) | no → yes: +2.8 pp |
| in_green_belt | 0.0001 (-0.0000 to 0.0002) | no → yes: -0.5 pp |
| mayor_1a_over_150_homes | 0.0000 (-0.0002 to 0.0002) | no → yes: +1.1 pp |
| social_rent_pct_major | 0.0000 (-0.0001 to 0.0001) | 0 → 28.5: +0.7 pp (10+ home schemes) |
| listed_building_within_25m | 0.0000 (-0.0006 to 0.0008) | no → yes: +1.7 pp |
| mayor_1c_height | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| is_major | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| has_communal_amenity | -0.0001 (-0.0002 to -0.0000) | no → yes: +0.7 pp |
| is_outline | -0.0001 (-0.0008 to 0.0006) | no → yes: -2.3 pp |
| has_demolition | -0.0001 (-0.0010 to 0.0009) | no → yes: +0.9 pp |
| has_studio | -0.0001 (-0.0004 to 0.0002) | no → yes: -0.6 pp |
| premium_amenity | -0.0001 (-0.0004 to 0.0001) | no → yes: +1.6 pp |
| statutory_major | -0.0006 (-0.0010 to -0.0001) | no → yes: -1.5 pp |
| has_backland | -0.0007 (-0.0018 to 0.0004) | no → yes: -4.4 pp |
| brownfield_site_within_50m | -0.0010 (-0.0032 to 0.0013) | no → yes: +4.0 pp |

