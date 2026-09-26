# Roof approval rate audit — 26 September 2026

## Finding

The claimed 75% approval for room extensions and 56% for new rooftop homes **has not been reproduced**. The figures originated in an earlier AI response, rather than a documented analysis. No original query, denominators or classification definitions have been supplied. Do not publish these figures as established facts. This audit does not prove that no defensible method could produce them; it finds that the supplied claim lacks a reproducible method.

The underlying dataset is real and available locally. Quick exploratory text filters produce materially different numbers, and are too imprecise to substitute as a validated room-versus-home comparison. Main recommendation: use the qualitative ROOM / HOME planning-route comparison; explain the missing evidence in the evidence panel.

## Source and provenance

- Audited source filename: `foundations_london_housing_2022_2025_20260810T013626Z.csv`.
- Official project dataset landing page: https://foreman.house-london.uk/
- Official dataset download: https://foreman.house-london.uk/download/csv/
- API schema: https://foreman.house-london.uk/api/schema/
- Data origin: House London's Foreman pipeline scrapes PlanIt records, then filters to `housing_relevance_score > 0.9`.
- Landing page fetched live on 26 September 2026 states 181,929 applications, 2022–2025, updated 10 August 2026.
- Live download response returned HTTP 200 and matched the local filename and content length of 115,473,911 bytes. This was a filename/size consistency check, not a remote byte-for-byte hash comparison.
- Locally parsed rows: 181,929; unique `name` values: 181,929. `start_date` range: 2022-01-01 to 2025-12-31.
- Local SHA-256: `fe425a1c1c5e95455a0861c75e0e7eb142f0f2d9c0b7ef22e448b74c474b840a`.
- `n_dwellings` is blank in 174,000 rows (about 95.6%). It cannot reliably separate added rooms from new dwellings.

Schema contains name, area_name, reference, uid, url, description, app_type, app_size, status, decision, decided_by, start_date, decided_date, target_decision_date, days_to_decision, last_changed, fetched_at, n_comments, n_documents, n_statutory_days, n_dwellings, housing_relevance_score, lat, lng, ward_name, agent_company, case_officer.

## Exploratory method

The full, exact regular expressions and a reproducible script are in `check_roof_rates.py`. Complete counts are in `roof_rate_audit.json`. No additional borough, year, dwelling-count or size selection was applied to the provided file.

1. Match description, case-insensitively, on these whole-word phrases: roof extension(s), loft conversion(s), mansard, dormer, roof enlargement, additional storey/storeys, upward extension.
2. New-home-language cohort: one of new/additional/create/creation/creating/provide/providing/form/formation/forming/comprising/accommodate, followed within 90 characters by dwelling(s), flat(s), apartment(s), residential unit(s) or self-contained unit(s); OR self-contained flat(s)/dwelling(s).
3. Room-language cohort: bedroom(s), room(s) in [the] roof, habitable, living accommodation, living space, additional accommodation; exclude any description meeting the new-home-language rule.
4. Main exploratory rows below restrict `app_type == 'Full'`.
5. Numerator: status `Permitted` OR `Conditions`. Denominator: those plus `Rejected`. Withdrawn, undecided, blank, unresolved and referred rows are excluded from denominator. Raw-decision inspection confirms that the normalized Conditions category includes grants with conditions; excluding it would wrongly remove many approvals. However, normalized status is not a perfect legal-outcome classification and was not manually audited record by record.
6. Sensitivity check additionally excludes descriptions mentioning prior approval, certificate of lawfulness, lawful development certificate, certificate of lawful, discharge/variation of condition(s), non-material amendment or minor material amendment.

| Exploratory text cohort | Granted / decided (`Full`) | Observed percentage | Granted / decided after procedural-text exclusion | Percentage |
|---|---:|---:|---:|---:|
| Roof keywords, all descriptions | 19,174 / 25,517 | 75.14% | 17,699 / 23,923 | 73.98% |
| Roof plus new-home language | 1,083 / 1,790 | 60.50% | 1,037 / 1,732 | 59.87% |
| Roof plus room language, without new-home language | 2,788 / 3,587 | 77.73% | 1,492 / 2,208 | 67.57% |
| Roof without new-home language | 18,091 / 23,727 | 76.25% | 16,662 / 22,191 | 75.08% |

These are diagnostic counts, **not substitute headline approval rates**. The marked sensitivity of the explicit-room cohort to procedural exclusions shows why simply selecting Full is insufficient.

## Classification pitfalls observed directly

- `app_type == 'Full'` does not reliably isolate ordinary full planning applications: procedural text exclusions materially change counts. The Outline category also contains lawful development certificates in directly inspected rows.
- Roof and new-home words can co-occur because a completely new house has a dormer, or because subdivision occurs elsewhere in the building. That does not mean a new independent home is created on the roof.
- Example false-positive risk: `Barking/22/00711/FULL` is a new two-storey house including a rear dormer, not an independent rooftop home above an existing building.
- Some descriptions quote previous permissions; keyword matches can identify historical rather than current works.
- Absence of new-home language is not proof that an application only adds rooms.
- The file is application-level. Different applications for the same site can remain; unique names do not prove unique schemes. Appeals, resubmissions, variations and certificates need separate treatment.
- The housing relevance score is a filtering/classification product, not a complete official census of every London planning application.
- Even validated cohort rates would show association, not prove that changing only use caused a refusal. Borough, design, route, heritage, scale and application mix differ.

## Recommended evidence-panel wording

“The earlier 75% / 56% comparison could not be reproduced from a documented method. We located and inspected the Foundations dataset, but its fields do not directly distinguish extra rooms from new rooftop homes. Keyword checks are sensitive to application type and can misclassify proposals. The comparison here explains planning routes; it does not predict an application's approval probability.”

If diagnostic rates are shown in a methods panel, retain the exact cohort labels and denominators above, and label them “exploratory text filters — not validated proposal categories.” Do not title them ROOM versus HOME.

## Saved audit files

- `check_roof_rates.py`: reproducible analysis.
- `roof_rate_audit.json`: full counts, method regexes, checksum and schema.
- `roof_new_language_samples.csv`: all 2,193 Full records meeting the broad new-home-language filter, with descriptions and original source URLs, for a later manual classification review.
- `foreman-home.html`: live source landing page.
- `foreman-about.html`: live methodology page.
- `api-schema.json`: live schema response; content is YAML despite the filename.
