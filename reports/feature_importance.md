# What drives the approval model

XGBoost approval model, 2025 test set (2,328 proposals, ROC-AUC 0.652). **ROC-AUC lost**: drop in ROC-AUC when the feature is shuffled (mean of 30, with 95% interval); **Effect**: change in mean predicted approval from a low to a high value (10th → 90th percentile of the model's input scale, or no → yes), everything else unchanged. Log-scale features (`log_*`) show log values. These are associations in historical decisions, not causal effects.

## Features with a real effect (interval above zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| Borough | 0.0883 (0.0702 to 0.1043) | 27% (Waltham Forest) to 70% (Haringey) for the same schemes |
| avg_home_size_m2 | 0.0096 (0.0055 to 0.0143) | 48.8 → 125: +6.2 pp |
| Unit mix (studio / 1b / 2b share) | 0.0075 (0.0029 to 0.0122) | studio -0.3 pp, 1b +2.0 pp, 2b +2.0 pp vs reference |
| Scheme type (HMO / student / co-living) | 0.0067 (0.0033 to 0.0095) | hmo -6.6 pp, student coliving +0.0 pp vs reference |
| space_std_share_below | 0.0064 (0.0013 to 0.0126) | 0 → 0.5: -3.0 pp |
| log_density | 0.0059 (0.0027 to 0.0091) | 3.01 → 5.25: -4.8 pp |
| log_homes_net | 0.0053 (0.0005 to 0.0099) | 0.693 → 2.08: -1.6 pp |
| in_conservation_area | 0.0026 (0.0006 to 0.0046) | no → yes: +2.8 pp |
| affordable_pct_major | 0.0019 (0.0001 to 0.0038) | 0 → 100: +20.3 pp (10+ home schemes) |
| Development type | 0.0013 (0.0004 to 0.0024) | change of use +0.4 pp, conversion -0.4 pp, extension +0.7 pp vs reference |
| has_pub_loss | 0.0007 (0.0002 to 0.0010) | no → yes: -3.3 pp |

## No clear effect (interval includes zero)

| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |
|---|---|---|
| log_homes_lost | 0.0034 (-0.0022 to 0.0081) | 0 → 0.693: +5.9 pp |
| has_basement | 0.0018 (-0.0002 to 0.0039) | no → yes: -5.1 pp |
| log_ptal | 0.0015 (-0.0020 to 0.0062) | 1.59 → 3.4: +0.3 pp |
| log_site_area | 0.0012 (-0.0039 to 0.0060) | 4.73 → 7.02: +4.6 pp |
| has_roof_terrace | 0.0006 (-0.0004 to 0.0015) | no → yes: +2.4 pp |
| in_article4_area | 0.0006 (-0.0000 to 0.0014) | no → yes: -0.3 pp |
| log_nonresi | 0.0005 (-0.0007 to 0.0016) | 0 → 4.31: -2.1 pp |
| storeys | 0.0003 (-0.0012 to 0.0020) | 2 → 4: +0.5 pp |
| social_rent_pct_major | 0.0002 (-0.0002 to 0.0005) | 0 → 28.5: +2.2 pp (10+ home schemes) |
| is_outline | 0.0002 (-0.0007 to 0.0011) | no → yes: -3.0 pp |
| in_opportunity_area | 0.0002 (-0.0001 to 0.0004) | no → yes: -0.1 pp |
| has_studio | 0.0001 (-0.0001 to 0.0003) | no → yes: -0.2 pp |
| has_commercial | 0.0001 (-0.0014 to 0.0012) | no → yes: +2.5 pp |
| mayor_1a_over_150_homes | 0.0000 (-0.0004 to 0.0003) | no → yes: +1.9 pp |
| Flood zone | 0.0000 (-0.0002 to 0.0003) | zone 2 +0.0 pp, zone 3 -0.6 pp vs reference |
| has_demolition | 0.0000 (-0.0008 to 0.0007) | no → yes: +0.7 pp |
| is_major | 0.0000 (-0.0000 to 0.0000) | no → yes: -0.0 pp |
| mayor_1c_height | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| in_green_belt | 0.0000 (0.0000 to 0.0000) | no → yes: +0.0 pp |
| premium_amenity | -0.0000 (-0.0002 to 0.0001) | no → yes: +1.0 pp |
| statutory_major | -0.0001 (-0.0004 to 0.0002) | no → yes: -0.7 pp |
| has_communal_amenity | -0.0001 (-0.0003 to 0.0000) | no → yes: +0.5 pp |
| brownfield_site_within_50m | -0.0002 (-0.0026 to 0.0027) | no → yes: +4.4 pp |
| imd_decile | -0.0003 (-0.0029 to 0.0015) | 2 → 9: +0.8 pp |
| listed_building_within_25m | -0.0003 (-0.0010 to 0.0006) | no → yes: +2.1 pp |
| in_town_centre | -0.0004 (-0.0019 to 0.0012) | no → yes: +2.9 pp |
| has_backland | -0.0009 (-0.0023 to 0.0003) | no → yes: -4.8 pp |

